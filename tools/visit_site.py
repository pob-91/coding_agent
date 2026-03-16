import json
from typing import Any

from utils.logger import get_logger
from utils.web import visit_webpage

logger = get_logger(__name__)


def visit_site(args: dict, item: Any) -> dict:
    if "url" not in args:
        logger.warning("Missing url arg for visit_site")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"error": "url argument is required"}),
        }

    try:
        result = visit_webpage(args["url"])
        if result.status_code != 200:
            return {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(
                    {
                        "error": f"Site visit failed with status code: {result.status_code}"
                    }
                ),
            }

        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": result.body,
        }
    except Exception as e:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Failed to visit webpage with error {e}",
                }
            ),
        }
