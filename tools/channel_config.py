import json
from typing import Any

from data.db_handler import DBHandler
from model.base_db_model import DBModelType
from model.channel_config import ChannelConfig
from utils.logger import get_logger

logger = get_logger(__name__)


def channel_config(args: dict, item: Any, channel_id: str) -> dict:
    if "repo_name" not in args:
        logger.warning("Missing repo_name arg for channel_config")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"error": "repo_name argument is required"}),
        }

    channel_config = ChannelConfig(
        type=DBModelType.CHANNEL_CONFIG,
        channel_id=channel_id,
        repo_name=args["repo_name"],
    )

    DBHandler.write_model(channel_config)

    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": "Channel config created successfully.",
    }
