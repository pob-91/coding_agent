import asyncio
import os
from typing import Any, Iterable

from openai import OpenAI

from data.db_handler import DBHandler
from data.open_router import OpenRouterHandler
from model.base_db_model import DBModelType
from model.channel_message import ChannelMessage
from utils.logger import get_logger
from utils.messages import convert_channel_messages

logger = get_logger(__name__)


async def run_planning_compaction(
    channel_id: str,
    configured_model: str | None = None,
) -> str:
    # Once an issue is posted we are going to compact all messages in the related channel

    with open("./agent_compact_system_prompt.txt", "r") as f:
        system_prompt = f.read()

    messages: Iterable[Any] = [{"role": "system", "content": system_prompt}]

    db_messages = DBHandler.get_channel_messages(channel_id=channel_id)
    historic_messages = convert_channel_messages(db_messages, flatten_tools=True)

    if len(historic_messages) == 0:
        logger.info("Nothing to compact...")
        return ""

    messages.extend(historic_messages)
    messages.append(
        {
            "role": "user",
            "content": "Now produce the compacted summary of the above conversation.",
        }
    )

    logger.info(f"Running compaction process on {len(messages)} messages")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=OpenRouterHandler.get_planning_model(configured_model=configured_model),
        messages=messages,
    )

    compacted = response.choices[0].message.content or ""

    if not compacted:
        logger.error("Failed to compact, got empty content.")
        return compacted

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
