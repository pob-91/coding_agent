import asyncio
import os
from typing import Any, Iterable

from openai import OpenAI

from data.db_handler import DBHandler
from model.base_db_model import DBModelType
from model.channel_message import ChannelMessage
from utils.logger import get_logger
from utils.messages import convert_channel_messages

logger = get_logger(__name__)


async def run_planning_compaction(channel_id: str) -> str:
    # Once an issue is posted we are going to compact all messages in the related channel

    with open("./agent_compact_system_prompt.txt", "r") as f:
        system_prompt = f.read()

    messages: Iterable[Any] = [{"role": "system", "content": system_prompt}]

    db_messages = DBHandler.get_channel_messages(channel_id=channel_id)
    historic_messages = convert_channel_messages(db_messages, flatten_tools=True)

    messages.extend(historic_messages)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )
    response = await asyncio.to_thread(
        client.responses.create,
        model=os.getenv("PLANNING_MODEL", ""),
        input=messages,
    )

    compacted = ""

    for item in response.output:
        if item.type != "message":
            logger.warning(
                f"Got item {item.type} in compaction response. Not handling."
            )
            continue

        for msg in item.content:
            if msg.type != "output_text":
                continue
            compacted += msg.text

    # Archive the current channel messages which takes them out of the view
    DBHandler.archive_channel_messages(channel_id)

    # Write the compacted message
    compacted_message = ChannelMessage(
        type=DBModelType.CHANNEL_MESSAGE,
        message_id=f"{db_messages[-1].message_id}_compacted",
        channel_id=channel_id,
        body=compacted,
        role="assistant",
    )
    DBHandler.write_model(compacted_message)

    return compacted
