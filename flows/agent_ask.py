import asyncio
import json
import os
import shutil
from typing import Any, Iterable

from openai import OpenAI

from model.pull_review_comment import PullReviewComment
from model.repository import Repository
from tools.list_files import list_files
from tools.read_file import read_file
from tools.respond import respond
from tools.search import search
from tools.tools import ask_tools
from utils.file import find_file, generate_top_level_file_tree
from utils.logger import get_logger
from utils.repo import clone_and_checkout, prep_url

logger = get_logger(__name__)


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
            context_blocks.append(f"File: {c.path}\n```diff\n{c.diff_hunk}\n```")
        parts.append("\nCode context from review:\n" + "\n\n".join(context_blocks))

    parts.append(f"\nQuestion: {question}")

    return "\n".join(parts)


async def run_agent_ask(
    question: str,
    repository: Repository,
    pr_number: int,
    branch: str,
    code_contexts: list[PullReviewComment] | None = None,
    source_comment_url: str | None = None,
) -> None:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )

    clone_url = prep_url(repository.clone_url)
    repo_url = prep_url(repository.url)

    repo_data = clone_and_checkout(
        repo_name=repository.name,
        clone_url=clone_url,
        branch_name=branch,
    )

    try:
        with open("./agent_ask_system_prompt.txt", "r") as f:
            system_prompt = f.read()

        agents_md: str | None = None
        agents_path = find_file(repo_data.local_path, "AGENTS.md")
        if agents_path:
            agents_path_str = agents_path
            with open(agents_path_str, "r") as f:
                agents_md = f.read()

        file_tree = generate_top_level_file_tree(repo_data.local_path)

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
                logger.warning(
                    "agent-ask exceeded max iterations without a respond call."
                )
                break

            response = await asyncio.to_thread(
                client.responses.create,
                model=os.getenv(
                    "AGENT_MODEL",
                    "moonshotai/kimi-k2-thinking",
                ),
                tools=ask_tools,
                input=messages,
            )
            calls += 1

            messages.extend(response.output)

            answered = False
            for item in response.output:
                if item.type != "function_call":
                    logger.info(f"Ignoring item in response: {item.type}")
                    continue

                try:
                    args: dict = json.loads(item.arguments)
                except json.JSONDecodeError as e:
                    logger.warning(f"agent-ask received invalid JSON arguments: {e}")
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {"error": f"Invalid JSON arguments: {e}"}
                            ),
                        }
                    )
                    continue

                logger.info(f"agent-ask calling: {item.name}, args: {item.arguments}")

                if item.name == "respond":
                    respond(
                        args,
                        item,
                        repo_url,
                        pr_number,
                        source_comment_url=source_comment_url,
                    )
                    answered = True
                elif item.name == "search":
                    messages.append(search(args, item, repo_data.local_path))
                elif item.name == "list_files":
                    messages.append(list_files(args, item, repo_data.local_path))
                elif item.name == "read_file":
                    messages.append(read_file(args, item, repo_data.local_path))
                else:
                    logger.warning(f"agent-ask received unknown tool call: {item.name}")

            if answered:
                break

    finally:
        try:
            shutil.rmtree(repo_data.local_path)
        except OSError as e:
            logger.warning(f"agent-ask failed to clean up repo: {e.strerror}")
