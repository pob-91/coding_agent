import asyncio
import json
from typing import Any

from flows.run_planning_compaction import run_planning_compaction
from utils.logger import get_logger

logger = get_logger(__name__)


def compact_chat(
    item: Any,
    channel_id: str,
    configured_model: str | None = None,
) -> dict:
    try:
        asyncio.run(
            run_planning_compaction(
                channel_id=channel_id,
                configured_model=configured_model,
            )
        )
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": "Chat compacted successfully.",
        }
    except Exception as e:
        logger.warning(f"Failed to compact chat: {e}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"error": f"Failed to compact chat: {e}"}),
        }
