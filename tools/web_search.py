import json
from typing import Any

from utils.logger import get_logger
from utils.web import search

logger = get_logger(__name__)


def web_search(args: dict, item: Any) -> dict:
    if "phrase" not in args:
        logger.warning("Missing phrase arg for web_search")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"error": "phrase argument is required"}),
        }

    try:
        results = search(phrase=args["phrase"])
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(results),
        }
    except Exception as e:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Failed to search the web with error {e}",
                }
            ),
        }
