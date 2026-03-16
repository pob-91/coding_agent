import asyncio
import json
import os
from typing import Any, Iterable

from openai import OpenAI

from data.db_handler import DBHandler
from model.base_db_model import DBModelType
from model.channel_message import ChannelMessage
from tools.channel_config import channel_config as cc
from tools.list_files import list_files
from tools.read_file import read_file
from tools.search import search
from tools.tools import planning_tools
from utils.logger import get_logger
from utils.prompt import build_planning_user_prompt
from utils.repo import CheckoutResponse, clone_and_checkout, prep_url
from utils.slack import send_slack_message

logger = get_logger(__name__)


# TODO: Add tool for the agent to list all branches
# TODO: Add tool for the agent to be able to search the web, there is a response type already in there, what is this?
# TODO: Add tool for the agent to be able to create an issue on the repo


class PlanningHandler:
    async def handle_event(self, payload: Any) -> None:
        team_id = payload.get("team_id")
        workspace_config = DBHandler.get_workspace_config(team_id=team_id)
        if workspace_config is None:
            logger.error(
                f"Cannot get workspace config for team: {team_id}. Cannot proceed."
            )
            return

        event = payload.get("event", {})
        if event.get("type") != "message":
            return
        if event.get("user") == workspace_config.bot_user_id:
            # Don't amswer our own messages!
            return
        if event.get("subtype") is not None:
            # New messages do not have this property
            return

        logger.info(f"Processing event: {event}")

        channel_id = event.get("channel")
        files = event.get("files")
        text = event.get("text")

        channel_config = DBHandler.get_channel_config(channel_id=channel_id)
        repo_data: CheckoutResponse | None = None

        if channel_config is not None:
            clone_url = self._create_clone_url(
                repo_name=channel_config.repo_name,
            )
            repo_data = clone_and_checkout(
                repo_name=channel_config.repo_name,
                clone_url=clone_url,
                is_planning_agent=True,
            )

        with open("./agent_plan_system_prompt.txt", "r") as f:
            system_prompt = f.read()

        messages: Iterable[Any] = [
            {"role": "system", "content": system_prompt},
        ]

        if repo_data is not None and channel_config is not None:
            user_prompt = build_planning_user_prompt(
                repo_name=channel_config.repo_name,
                current_branch=repo_data.repo.active_branch.name,
                local_path=repo_data.local_path,
            )
            messages.append({"role": "user", "content": user_prompt})

        db_messages = DBHandler.get_channel_messages(channel_id=channel_id)
        historic_messages: Iterable[Any] = [
            {"role": msg.role, "content": msg.body} for msg in db_messages
        ]

        all_messages = messages + historic_messages

        if text == "" and len(files) > 0:
            send_slack_message(
                channel_id=channel_id,
                text="We will be handling audio recordings shortly... Until then just toodle along little human.",
                token=workspace_config.access_token,
            )
            return
        elif len(text) > 0:
            channel_message = ChannelMessage(
                type=DBModelType.CHANNEL_MESSAGE,
                channel_id=channel_id,
                index=len(all_messages),
                body=text,
                role="user",
            )
            DBHandler.write_model(channel_message)
            all_messages.append({"role": "user", "content": text})
        else:
            send_slack_message(
                channel_id=channel_id,
                text="Messages of that type cannot be handled yet. Sorry... Go back to burping and chewing little human.",
                token=workspace_config.access_token,
            )
            return

        if channel_config is None:
            all_messages.append(
                {
                    "role": "system",
                    "content": "IMPORTANT! The user has not yet configued the channel config so we cannot help them yet. Acknowledge their message but ask that they first provide you with the repo name in the format user/repo. We have the base repo URL so we will handle making sure it can work. Once they have given the repo name, call the channel_config tool and pass it as an argument.",
                }
            )

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPEN_ROUTER_API_KEY"),
        )

        return_message: str = ""
        answered: bool = False

        while True:
            response = await asyncio.to_thread(
                client.responses.create,
                model=os.getenv(
                    "PLANNING_MODEL",
                    "openai/gpt-5.4",
                ),
                tools=planning_tools,
                input=messages,
            )

            for item in response.output:
                if item.type == "message":
                    for msg in item.content:
                        if msg.type != "output_text":
                            continue
                        return_message += msg.text
                    answered = True
                    break

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
                                {
                                    "error": f"Invalid JSON arguments: {e}. Args must be JSON objects that adhere to the tool properties structure."
                                }
                            ),
                        }
                    )
                    continue

                logger.info(
                    f"planning-handler calling: {item.name}, args: {item.arguments}"
                )

                if item.name == "channel_config":
                    messages.append(
                        cc(
                            args=args,
                            item=item,
                            channel_id=channel_id,
                        )
                    )
                elif repo_data is None:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": f"Cannot call function: {item.name} as there is no repo associated with the channel. Get the repo name in the format user/repo_name an call the channel_config tool.",
                        }
                    )
                elif item.name == "search":
                    messages.append(search(args, item, repo_data.local_path))
                elif item.name == "list_files":
                    messages.append(list_files(args, item, repo_data.local_path))
                elif item.name == "read_file":
                    messages.append(read_file(args, item, repo_data.local_path))
                else:
                    logger.warning(
                        f"planning-agent received unknown tool call: {item.name}"
                    )

            if answered:
                break

        send_slack_message(
            channel_id=channel_id,
            text=return_message,
            token=workspace_config.access_token,
        )

    def _create_clone_url(self, repo_name: str) -> str:
        return prep_url(f"{os.getenv('REPO_BASE_URL')}/{repo_name}.git")
