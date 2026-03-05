import json
from typing import Any

from utils.logger import get_logger
from utils.search import regex_search

logger = get_logger(__name__)


def search(args: dict, item: Any, local_path: str) -> dict:
    if "query" not in args:
        logger.warning("query not in args for search function")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {"error": "query argument not given to function call search"}
            ),
        }

    results = regex_search(
        local_path,
        args["query"],
        args.get("sub_path", None),
    )

    logger.info(f"Returned results of search function: {json.dumps(results)}")
    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": json.dumps(results),
    }
