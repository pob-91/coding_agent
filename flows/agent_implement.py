import asyncio
import json
import os
import shutil
from dataclasses import dataclass
from typing import Any, Iterable, Literal

from openai import OpenAI

from model.issue import Issue
from model.pull_review_comment import PullReviewComment
from model.repository import Repository
from tools.create_file import create_file
from tools.delete_text import delete_text
from tools.insert_after import insert_after
from tools.list_files import list_files
from tools.read_file import read_file
from tools.replace_text import replace_text
from tools.search import search
from tools.tools import issue_tools
from utils.logger import get_logger
from utils.prompt import build_implement_user_prompt
from utils.repo import (
    CheckoutResponse,
    clone_and_checkout,
    comment_on_issue,
    commit_changes_and_push,
    create_pull_request,
    post_on_pr,
    prep_issue_branch_name,
    prep_url,
)

logger = get_logger(__name__)


@dataclass
class PRSource:
    pr_number: int
    branch: str
    source_comment_url: str | None
    code_contexts: list[PullReviewComment] | None


@dataclass
class ImplementationSource:
    source: Literal["issue", "pr"]
    issue: Issue | None
    pr: PRSource | None


def _branch_name(source: ImplementationSource) -> str:
    if source.pr is not None:
        return source.pr.branch

    if source.issue is not None:
        return prep_issue_branch_name(issue_title=source.issue.title)

    raise Exception("AHHHHH!")


async def _wrap_up(
    source: ImplementationSource,
    repo_url: str,
    repository: Repository,
    repo_data: CheckoutResponse,
    commit_message: str | None,
) -> None:
    if source.issue is not None:
        if not create_pull_request(
            repo_url=repo_url,
            base_branch=repository.default_branch,
            issue_branch=repo_data.branch_name,
            issue_title=source.issue.title,
        ):
            logger.warning("Failed to create pull request for issue.")

        issue_url = f"{repo_url}/issues/{source.issue.number}"
        if not comment_on_issue(commit_message, issue_url):
            logger.warning("Failed to comment on issue.")
        return

    if source.pr is not None:
        if not post_on_pr(
            agent_comment=f"Implemeted agent-update flow: {commit_message}",
            repo_url=repo_url,
            pr_number=source.pr.pr_number,
            source_comment_url=source.pr.source_comment_url,
        ):
            logger.warning("Failed to comment on PR.")
        return

    raise Exception("Pooooo!")


async def run_agent_implement(
    agent_command: str,
    repository: Repository,
    source: ImplementationSource,
) -> None:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )

    clone_url = prep_url(repository.clone_url)
    repo_url = prep_url(repository.url)

    branch_name = _branch_name(source)
    repo_data = clone_and_checkout(
        repo_name=repository.name,
        clone_url=clone_url,
        branch_name=branch_name,
    )

    with open("./agent_implement_system_prompt.txt", "r") as f:
        system_prompt = f.read()

    user_prompt = build_implement_user_prompt(
        repository=repository,
        local_path=repo_data.local_path,
        issue=source.issue,
        agent_command=agent_command,
        code_contexts=source.pr.code_contexts if source.pr is not None else None,
    )

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
            logger.warning("Calls exceeded 100 iterations. Perhaps increase the limit.")
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

            try:
                args: dict = json.loads(item.arguments)
            except json.JSONDecodeError as e:
                logger.warning(f"Received invalid JSON arguments: {e}")
                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(
                            {
                                "error": f"Invalid JSON arguments: {e}. Args must be JSON objects that adhere to the tool properties structure."
                            }
                        ),
                    }
                )
                continue

            logger.info(f"Calling function: {item.name}, with args: {item.arguments}")

            if item.name == "create_file":
                messages.append(create_file(args, item, repo_data.local_path))
                continue
            if item.name == "search":
                messages.append(search(args, item, repo_data.local_path))
                continue
            if item.name == "list_files":
                messages.append(list_files(args, item, repo_data.local_path))
                continue
            if item.name == "read_file":
                messages.append(read_file(args, item, repo_data.local_path))
                continue
            if item.name == "replace_text":
                messages.append(replace_text(args, item, repo_data.local_path))
                continue
            if item.name == "insert_after":
                messages.append(insert_after(args, item, repo_data.local_path))
                continue
            if item.name == "delete_text":
                messages.append(delete_text(args, item, repo_data.local_path))
                continue
            if item.name == "commit":
                execute = False
                if "commit_message" in args:
                    commit_message = args["commit_message"]
                logger.info("Received commit call, finalising changes.")

    if success:
        commit_changes_and_push(
            repo=repo_data.repo,
            branch_name=branch_name,
            first_push=repo_data.first_push,
            commit_message=commit_message,
        )

        await _wrap_up(
            source=source,
            repo_url=repo_url,
            repository=repository,
            repo_data=repo_data,
            commit_message=commit_message,
        )

    try:
        shutil.rmtree(repo_data.local_path)
    except OSError as e:
        logger.warning(f"Failed to clean up and delete repo on disk: {e.strerror}")
