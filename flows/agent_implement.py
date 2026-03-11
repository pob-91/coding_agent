import asyncio
import json
import os
import shutil
import uuid
from typing import Any, Iterable

from git import Repo
from openai import OpenAI

from model.issue import Issue
from model.repository import Repository
from tools.create_file import create_file
from tools.delete_text import delete_text
from tools.insert_after import insert_after
from tools.list_files import list_files
from tools.read_file import read_file
from tools.replace_text import replace_text
from tools.search import search
from tools.tools import issue_tools
from utils.file import find_file, generate_top_level_file_tree
from utils.logger import get_logger
from utils.repo import (
    checkout_issue_branch,
    comment_on_issue,
    commit_changes_and_push,
    create_pull_request,
    prep_url,
)

logger = get_logger(__name__)


async def run_agent_implement(
    agent_command: str,
    repository: Repository,
    issue: Issue,
) -> None:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )

    clone_url = prep_url(repository.clone_url)
    repo_url = prep_url(repository.url)

    local_path = f"/tmp/{str(uuid.uuid4())}/{repository.name}"
    repo = Repo.clone_from(
        clone_url,
        local_path,
        depth=1,
    )

    try:
        repo.git.checkout("main")
    except Exception:
        pass  # Already on main branch

    with open("./issue_comment_system_prompt.txt", "r") as f:
        system_prompt = f.read()

    with open("./issue_comment_user_prompt_template.txt", "r") as f:
        user_prompt = f.read()

    user_prompt = user_prompt.replace("{{repo_name}}", repository.name)

    file_tree = generate_top_level_file_tree(local_path)
    user_prompt = user_prompt.replace("{{file_tree}}", file_tree)

    agents_path = find_file(local_path, "AGENTS.md")
    if agents_path is not None:
        logger.info("Found AGENTS.md, adding to user prompt.")
        with open(agents_path, "r") as f:
            agents_content = f.read()
            user_prompt = user_prompt.replace(
                "{{agents_md_content}}",
                f"START AGENTS_MD --{agents_content}-- END AGENTS_MD",
            )
    else:
        user_prompt = user_prompt.replace("{{agents_md_content}}", "No AGENTS.md provided.")

    user_prompt = user_prompt.replace("{{issue_title}}", issue.title)
    user_prompt = user_prompt.replace("{{issue_body}}", issue.body)

    agent_command = agent_command.strip()
    user_prompt = user_prompt.replace("{{agent_command}}", agent_command)

    issue_branch, first_push = checkout_issue_branch(repo, issue.title)

    messages: Iterable[Any] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    logger.info(f"Sending initial message to agent: {json.dumps(messages)}")

    commit_message: str | None = None
    calls = 0
    max_calls = 100
    execute = True
    success = True

    while execute:
        if calls >= max_calls:
            logger.warning(
                "Calls exceeded 100 iterations. Perhaps let the model know or increase the limit."
            )
            commit_message = "Agent flow exceeded 100 iterations, failed to implement."
            execute = False
            success = False
            break

        response = await asyncio.to_thread(
            client.responses.create,
            model=os.getenv("AGENT_MODEL", "moonshotai/kimi-k2-thinking"),
            tools=issue_tools,
            input=messages,
        )
        calls += 1

        if calls % 10 == 0:
            messages.append(
                {
                    "role": "user",
                    "content": f"You have now used {calls} of a maximum {max_calls} tool calls.",
                }
            )
        if max_calls - calls < 10:
            messages.append(
                {
                    "role": "user",
                    "content": f"You have now used {calls} of a maximum {max_calls} tool calls. Probably time to wrap up.",
                }
            )

        messages.extend(response.output)

        for item in response.output:
            if item.type != "function_call":
                logger.info(f"Ignoring item in response: {item.type}")
                continue

            args: dict = json.loads(item.arguments)
            logger.info(f"Calling function: {item.name}, with args: {item.arguments}")

            if item.name == "create_file":
                messages.append(create_file(args, item, local_path))
                continue
            if item.name == "search":
                messages.append(search(args, item, local_path))
                continue
            if item.name == "list_files":
                messages.append(list_files(args, item, local_path))
                continue
            if item.name == "read_file":
                messages.append(read_file(args, item, local_path))
                continue
            if item.name == "replace_text":
                messages.append(replace_text(args, item, local_path))
                continue
            if item.name == "insert_after":
                messages.append(insert_after(args, item, local_path))
                continue
            if item.name == "delete_text":
                messages.append(delete_text(args, item, local_path))
                continue
            if item.name == "commit":
                execute = False
                if "commit_message" in args:
                    commit_message = args["commit_message"]
                logger.info("Received commit call, finalising changes.")

    if success:
        commit_changes_and_push(
            repo,
            issue_branch,
            first_push,
            commit_message,
        )

        if not await create_pull_request(
            repo_url,
            repository.default_branch,
            issue_branch,
            issue.title,
        ):
            logger.warning("Failed to create pull request for issue.")

        issue_url = f"{repo_url}/issues/{issue.number}"
        if not comment_on_issue(commit_message, issue_url):
            logger.warning("Failed to comment on issue.")

    try:
        shutil.rmtree(local_path)
    except OSError as e:
        logger.warning(f"Failed to clean up and delete repo on disk: {e.strerror}")