import json
import os
import shutil
import uuid
from typing import Any, Iterable

from git import Repo
from openai import OpenAI

from handlers.base_handler import BaseHandler
from model.issue_comment import IssueComment
from model.webhook_message import WebhookMessage
from tools.delete_text import delete_text
from tools.insert_after import insert_after
from tools.list_files import list_files
from tools.read_file import read_file
from tools.replace_text import replace_text
from tools.search import search
from tools.tools import tools
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


class IssueCommentHandler(BaseHandler):
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPEN_ROUTER_API_KEY"),
        )

    async def handle(self, data: WebhookMessage) -> None:
        issue_comment: IssueComment = data  # type: ignore[assignment]

        comment = issue_comment.comment.body.strip()
        if not comment.startswith("/agent-implement"):
            logger.info("Issue comment not targeted at agents.")
            return

        command = comment.removeprefix("/agent-implement")
        logger.info(f"Handling agent command: {command}")

        clone_url = prep_url(issue_comment.repository.clone_url)
        repo_url = prep_url(issue_comment.repository.url)

        repo: Repo
        local_path = f"/tmp/{str(uuid.uuid4())}/{issue_comment.repository.name}"
        repo = Repo.clone_from(
            clone_url,
            local_path,
            depth=1,
        )

        try:
            repo.git.checkout("main")
        except Exception:
            pass  # Already on main branch

        with open("./system_prompt.txt", "r") as f:
            system_prompt = f.read()

        with open("./user_prompt_template.txt", "r") as f:
            user_prompt = f.read()

        user_prompt = user_prompt.replace("{{repo_name}}", issue_comment.repository.name)

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
            user_prompt = user_prompt.replace(
                "{{agents_md_content}}", "No AGENTS.md provided."
            )

        user_prompt = user_prompt.replace("{{issue_title}}", issue_comment.issue.title)
        user_prompt = user_prompt.replace("{{issue_body}}", issue_comment.issue.body)

        agent_command = issue_comment.comment.body.strip()
        agent_command = agent_command.removeprefix("/agent-implement")
        agent_command = agent_command.strip()
        user_prompt = user_prompt.replace("{{agent_command}}", agent_command)

        # NOTE: If useful can either add the most recent N comments to the user prompt or pass them all to a model to summarise
        # and then add that the user prompt.
        # For now just keeping it clean and relying on the issue body.

        issue_branch, first_push = checkout_issue_branch(repo, issue_comment.issue.title)

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

            response = self.client.responses.create(
                model=os.getenv("AGENT_MODEL", "moonshotai/kimi-k2-thinking"),
                tools=tools,
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
                    logger.info(f"Ingoring item in response: {item.type}")
                    continue

                args: dict = json.loads(item.arguments)
                logger.info(f"Calling function: {item.name}, with args: {item.arguments}")

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
                    logger.info("Recieved commit call, finalising changes.")

        if success:
            commit_changes_and_push(
                repo,
                issue_branch,
                first_push,
                commit_message,
            )

            if not await create_pull_request(
                repo_url,
                issue_comment.repository.default_branch,
                issue_branch,
                issue_comment.issue.title,
            ):
                logger.warning("Failed to create pull request for issue.")

            if not comment_on_issue(commit_message, clone_url):
                logger.warning("Failed to comment on issue.")

        try:
            shutil.rmtree(local_path)
        except OSError as e:
            logger.warning(f"Failed to clean up and delete repo on disk: {e.strerror}")
