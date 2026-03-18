import asyncio
import json
import os
from typing import Any, Iterable, Literal

from openai import OpenAI

from data.db_handler import DBHandler
from model.base_db_model import DBModelType
from model.channel_config import ChannelConfig
from model.channel_message import ChannelMessage
from tools.channel_config import channel_config as cc
from tools.checkout_branch import checkout_branch
from tools.list_branches import list_branches
from tools.list_files import list_files
from tools.post_issue import post_issue
from tools.read_file import read_file
from tools.search import search
from tools.tools import planning_tools
from tools.visit_site import visit_site
from tools.web_search import web_search
from utils.logger import get_logger
from utils.prompt import build_planning_user_prompt
from utils.repo import CheckoutResponse, clone_and_checkout, prep_url
from utils.slack import send_slack_message
from utils.time import generate_ts

logger = get_logger(__name__)


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
        channel_id = event.get("channel")
        files = event.get("files")
        text = event.get("text")
        message_id = event.get("ts")

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

        messages = self._prep_messages(
            repo_data=repo_data,
            channel_config=channel_config,
            channel_id=channel_id,
        )

        if event.get("type") != "message":
            return
        if event.get("user") == workspace_config.bot_user_id:
            # Don't amswer our own messages!
            return
        if event.get("subtype") is not None:
            # New messages do not have this property
            if event.get("subtype") == "message_deleted":
                id = event["previous_message"]["ts"]
                DBHandler.delete_channel_message(id)
                return
            if event.get("subtype") == "message_changed":
                original_ts = payload["event"]["message"]["ts"]
                new_content = payload["event"]["message"]["text"]
                DBHandler.update_channel_message(original_ts, new_content)
                return
            return

        logger.info(f"Processing event: {event}")

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
                message_id=message_id,
                channel_id=channel_id,
                body=text,
                role="user",
            )
            DBHandler.write_model(channel_message)
            messages.append({"role": "user", "content": text})
        else:
            send_slack_message(
                channel_id=channel_id,
                text="Messages of that type cannot be handled yet. Sorry... Go back to burping and chewing little human.",
                token=workspace_config.access_token,
            )
            return

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPEN_ROUTER_API_KEY"),
        )

        while True:
            response = await asyncio.to_thread(
                client.responses.create,
                model=os.getenv("PLANNING_MODEL", ""),
                tools=planning_tools,
                input=messages,
            )

            if response.status == "completed":
                message = ""
                for item in response.output:
                    if item.type != "message":
                        continue
                    for msg in item.content:
                        if msg.type != "output_text":
                            continue
                        message += msg.text
                if len(message) > 0:
                    send_slack_message(
                        channel_id=channel_id,
                        text=message,
                        token=workspace_config.access_token,
                    )
                break

            has_tool_calls = False
            for item in response.output:
                if item.type == "message":
                    message = ""
                    for msg in item.content:
                        if msg.type != "output_text":
                            continue
                        message += msg.text
                    if len(message) > 0:
                        send_slack_message(
                            channel_id=channel_id,
                            text=message,
                            token=workspace_config.access_token,
                        )
                    continue

                if item.type != "function_call":
                    logger.info(f"Ignoring item in response: {item.type}")
                    continue

                has_tool_calls = True

                messages.extend(response.output)
                self._save_internal_tool_message(
                    channel_id=channel_id,
                    role="tool_call",
                    call_id=item.call_id,
                    tool_name=item.name,
                    content=json.dumps(response.output),
                )

                try:
                    args: dict = json.loads(item.arguments)
                except json.JSONDecodeError as e:
                    logger.warning(f"agent-ask received invalid JSON arguments: {e}")
                    tool_response = {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(
                            {
                                "error": f"Invalid JSON arguments: {e}. Args must be JSON objects that adhere to the tool properties structure."
                            }
                        ),
                    }
                    messages.append(tool_response)
                    self._save_internal_tool_message(
                        channel_id=channel_id,
                        role="tool_output",
                        call_id=item.call_id,
                        tool_name=item.name,
                        content=json.dumps(tool_response),
                    )
                    continue

                logger.info(
                    f"planning-handler calling: {item.name}, args: {item.arguments}"
                )

                tool_response: dict = {}
                save = True

                if item.name == "channel_config":
                    tool_response = cc(
                        args=args,
                        item=item,
                        channel_id=channel_id,
                    )
                elif repo_data is None or channel_config is None:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": f"Cannot call function: {item.name} as there is no repo associated with the channel. Get the repo name in the format user/repo_name an call the channel_config tool.",
                        }
                    )
                elif item.name == "search":
                    tool_response = search(args, item, repo_data.local_path)
                elif item.name == "list_files":
                    tool_response = list_files(args, item, repo_data.local_path)
                elif item.name == "read_file":
                    tool_response = read_file(args, item, repo_data.local_path)
                elif item.name == "checkout_branch":
                    tool_response = checkout_branch(args, item, repo_data.repo)
                elif item.name == "list_branches":
                    tool_response = list_branches(args, item, repo_data.repo)
                elif item.name == "web_search":
                    tool_response = web_search(args, item)
                elif item.name == "visit_site":
                    tool_response = visit_site(args, item)
                elif item.name == "post_issue":
                    repo_url = self._create_repo_url(channel_config.repo_name)
                    tool_response = post_issue(args, item, repo_url)
                else:
                    save = False
                    logger.warning(
                        f"planning-agent received unknown tool call: {item.name}"
                    )

                if save:
                    messages.append(tool_response)
                    self._save_internal_tool_message(
                        channel_id=channel_id,
                        role="tool_output",
                        call_id=item.call_id,
                        tool_name=item.name,
                        content=json.dumps(tool_response),
                    )

            if not has_tool_calls:
                # This should never happen - or odd if it does
                break

    def _create_clone_url(self, repo_name: str) -> str:
        return prep_url(
            os.path.join(
                os.getenv("REPO_BASE_URL", ""),
                f"{repo_name}.git",
            )
        )

    def _create_repo_url(self, repo_name: str) -> str:
        return prep_url(
            os.path.join(
                os.getenv("REPO_BASE_URL", ""),
                "api/v1/repos",
                repo_name,
            )
        )

    def _prep_messages(
        self,
        repo_data: CheckoutResponse | None,
        channel_config: ChannelConfig | None,
        channel_id: str,
    ) -> list:
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

        if channel_config is None:
            messages.append(
                {
                    "role": "user",
                    "content": "IMPORTANT! The user has not yet configued the channel config so we cannot help them yet. Acknowledge their message but ask that they first provide you with the repo name in the format user/repo. We have the base repo URL so we will handle making sure it can work. Once they have given the repo name, call the channel_config tool and pass it as an argument.",
                }
            )
        else:
            messages.append(
                {
                    "role": "user",
                    "content": f"IMPORTANT! You are connected to the {channel_config.repo_name} repo so you do not need to ask the user for the repo name or call channel_config.",
                }
            )

        db_messages = DBHandler.get_channel_messages(channel_id=channel_id)

        historic_messages: Iterable[Any] = []
        for msg in db_messages:
            if msg.role == "user":
                historic_messages.append({"role": "user", "content": msg.body})
            elif msg.role == "assistant":
                historic_messages.append({"role": "assistant", "content": msg.body})
            elif msg.role == "tool_call":
                historic_messages.append(
                    {
                        "type": "function_call",
                        "call_id": msg.call_id,
                        "name": msg.tool_name,
                        "arguments": msg.body,
                    }
                )
            elif msg.role == "tool_output":
                historic_messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": msg.call_id,
                        "output": msg.body,
                    }
                )

        return messages + historic_messages

    def _save_internal_tool_message(
        self,
        channel_id: str,
        role: Literal["tool_call", "tool_output"],
        call_id: str,
        tool_name: str,
        content: str,
    ) -> None:
        message = ChannelMessage(
            type=DBModelType.CHANNEL_MESSAGE,
            channel_id=channel_id,
            message_id=generate_ts(),
            body=content,
            role=role,
            call_id=call_id,
            tool_name=tool_name,
        )
        DBHandler.write_model(message)
