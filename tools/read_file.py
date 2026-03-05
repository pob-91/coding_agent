import json
from typing import Any

from utils.file import read_file as rf
from utils.logger import get_logger

logger = get_logger(__name__)


def read_file(args: dict, item: Any, local_path: str) -> dict:
    if "path" not in args:
        logger.warning("path not in args for read file function")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {"error": "path argument not given to function call search"}
            ),
        }

    start: int = args.get("start_line", 1)
    end: int = args.get("end_line", -1)
    if end == -1:
        end = start + 50

    if start < 1:
        logger.warning("start < 0 for read file functio")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": "start_line must be >= 1",
                }
            ),
        }
    if start >= end:
        logger.warning("end not > than start for read file function")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": "end_line must be > than start_line",
                }
            ),
        }

    try:
        results = rf(
            local_path,
            args["path"],
            start,
            end,
        )
        logger.info(f"Returned results of read file function: {json.dumps(results)}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(results),
        }
    except FileNotFoundError:
        logger.warning(f"File not found with path: {args['path']}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"File not found with path {args['path']}",
                }
            ),
        }
