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
from utils.slack import send_slack_message

logger = get_logger(__name__)


# TODO: Generate a system prompt and optionally a user prompt about the repo
# TODO: Work out how to make sure that the message.text in the response is the last thing in the chain
# TODO: If there is a channel_config, checkout the repo at the /tmp/planning/repo path if it does not already exist
# TODO: Fetch and pull on the repo and checkout main
# TODO: Add tool for the agent to checkout a different branch
# TODO: Add tool for the agent to be able to search the web, there is a response type already in there, what is this?


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
        logger.info(f"{event}")
        if event.get("type") != "message":
            return

        channel_id = event.get("channel")
        files = event.get("files")
        text = event.get("text")

        channel_config = DBHandler.get_channel_config(channel_id=channel_id)

        messages: Iterable[Any] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
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
                    "AGENT_MODEL",
                    "moonshotai/kimi-k2-thinking",
                ),
                tools=planning_tools,
                input=messages,
            )

            for item in response.output:
                if item.type == "message":
                    for msg in item.content:
                        return_message += str(msg.text)
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
