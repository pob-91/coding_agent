import json
from typing import Any

from utils.file import create_file as cf
from utils.logger import get_logger

logger = get_logger(__name__)


def create_file(args: dict, item: Any, local_path: str) -> dict:
    if "path" not in args:
        logger.warning("Missing path arg for create_file")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"error": "path argument is required"}),
        }

    try:
        cf(local_path, args["path"], args.get("text", ""))
        logger.info(f"Created file {args['path']}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": f"{args['path']} created successfully.",
        }
    except FileExistsError:
        logger.warning(f"File already exists: {args['path']}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"error": f"File already exists: {args['path']}"}),
        }
