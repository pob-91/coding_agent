import json
from typing import Any

from utils.file import generate_top_level_file_tree
from utils.logger import get_logger

logger = get_logger(__name__)


def list_files(args: dict, item: Any, local_path: str) -> dict:
    if "path" not in args:
        logger.warning("path not in args for list_files function")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {"error": "path argument not given to function call search"}
            ),
        }

    try:
        results = generate_top_level_file_tree(local_path, args["path"])
        logger.info(f"Returned results of list files function: {json.dumps(results)}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(results),
        }
    except FileNotFoundError:
        logger.warning("path not in args for list_files function")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Path {args['path']} not found.",
                }
            ),
        }
