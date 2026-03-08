import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Iterable

from git import Repo
from openai import OpenAI

from model.pull_review_comment import PullReviewComment
from model.repository import Repository
from tools.list_files import list_files
from tools.read_file import read_file
from tools.search import search
from utils.file import find_file, generate_top_level_file_tree
from utils.logger import get_logger
from utils.repo import comment_on_issue, prep_url

logger = get_logger(__name__)

_SYSTEM_PROMPT_PATH = Path(__file__).parent / "agent_ask_system_prompt.txt"

_ask_tools: Iterable[Any] = [
    {
        "type": "function",
        "name": "search",
        "description": "Search repository using regex.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Regex pattern to search."},
                "sub_path": {"type": "string", "description": "Optional sub-path relative to repo root."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_files",
        "description": "List files and directories at a given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path relative to repo root."},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Read a portion of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root."},
                "start_line": {"type": "integer", "description": "Line to start reading from. Defaults to 1."},
                "end_line": {"type": "integer", "description": "Line to stop reading. Defaults to start_line + 50."},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "respond",
        "description": "Submit your final answer. Call this once you have sufficient context to answer the question.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "description": "The answer to post as a comment on the pull request."},
            },
            "required": ["answer"],
            "additionalProperties": False,
        },
    },
]


def _build_user_prompt(
    repo_name: str,
    file_tree: str,
    agents_md: str | None,
    code_contexts: list[PullReviewComment],
    question: str,
) -> str:
    parts = [
        f"Repository: {repo_name}",
        f"\nRepository structure:\n{file_tree}",
    ]

    if agents_md:
        parts.append(f"\nRepository Guidelines (AGENTS.md):\n{agents_md}")

    if code_contexts:
        context_blocks = []
        for c in code_contexts:
            context_blocks.append(
                f"File: {c.path}\n```diff\n{c.diff_hunk}\n```"
            )
        parts.append("\nCode context from review:\n" + "\n\n".join(context_blocks))

    parts.append(f"\nQuestion: {question}")

    return "\n".join(parts)


async def run_agent_ask(
    question: str,
    repository: Repository,
    pr_number: int,
    code_contexts: list[PullReviewComment] | None = None,
) -> None:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )

    clone_url = prep_url(repository.clone_url)
    repo_url = prep_url(repository.url)

    local_path = f"/tmp/{uuid.uuid4()}/{repository.name}"
    repo = Repo.clone_from(clone_url, local_path, depth=1)

    try:
        repo.git.checkout("main")
    except Exception:
        pass

    try:
        system_prompt = _SYSTEM_PROMPT_PATH.read_text()

        agents_md: str | None = None
        agents_path = find_file(local_path, "AGENTS.md")
        if agents_path:
            agents_path_str = agents_path
            with open(agents_path_str, "r") as f:
                agents_md = f.read()

        file_tree = generate_top_level_file_tree(local_path)

        user_prompt = _build_user_prompt(
            repo_name=repository.name,
            file_tree=file_tree,
            agents_md=agents_md,
            code_contexts=code_contexts or [],
            question=question,
        )

        messages: Iterable[Any] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        calls = 0
        max_calls = 30

        while True:
            if calls >= max_calls:
                logger.warning("agent-ask exceeded max iterations without a respond call.")
                break

            response = client.responses.create(
                model=os.getenv("AGENT_MODEL", "moonshotai/kimi-k2-thinking"),
                tools=_ask_tools,
                input=messages,
            )
            calls += 1

            messages.extend(response.output)

            answered = False
            for item in response.output:
                if item.type != "function_call":
                    logger.info(f"Ignoring item in response: {item.type}")
                    continue

                args: dict = json.loads(item.arguments)
                logger.info(f"agent-ask calling: {item.name}, args: {item.arguments}")

                if item.name == "respond":
                    answer = args.get("answer", "")
                    issue_url = f"{repo_url}/issues/{pr_number}"
                    if not comment_on_issue(answer, issue_url):
                        logger.warning("agent-ask failed to post answer as comment.")
                    answered = True
                    break

                if item.name == "search":
                    messages.append(search(args, item, local_path))
                elif item.name == "list_files":
                    messages.append(list_files(args, item, local_path))
                elif item.name == "read_file":
                    messages.append(read_file(args, item, local_path))
                else:
                    logger.warning(f"agent-ask received unknown tool call: {item.name}")

            if answered:
                break

    finally:
        try:
            shutil.rmtree(local_path)
        except OSError as e:
            logger.warning(f"agent-ask failed to clean up repo: {e.strerror}")
