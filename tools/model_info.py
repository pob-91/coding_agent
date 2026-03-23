import json
from typing import Any

from data.open_router import OpenRouterHandler
from utils.logger import get_logger

logger = get_logger(__name__)


def model_info(args: dict, item: Any) -> dict:
    if "model_id" not in args:
        logger.warning("model_id not in args for model_info function")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {"error": "model_id argument not given to function call model_info"}
            ),
        }

    try:
        model = OpenRouterHandler.get_model_info(args["model_id"])
        if model is None:
            return {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(
                    {"error": f"Model not found: {args['model_id']}"}
                ),
            }

        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": model.model_dump_json(),
        }
    except Exception as e:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {"error": f"Failed to get model info with error {e}"}
            ),
        }
