import json
from typing import Any

from utils.file import insert_after as ia
from utils.logger import get_logger

logger = get_logger(__name__)


def insert_after(args: dict, item: Any, local_path: str) -> dict:
    missing_args: list[str] = []
    if "path" not in args:
        missing_args.append("path")
    if "search" not in args:
        missing_args.append("search")
    if "text" not in args:
        missing_args.append("text")

    if len(missing_args) > 0:
        logger.warning(f"Missing args for insert_after: {missing_args}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"the following arguments are required but missing: {missing_args}",
                }
            ),
        }

    try:
        success = ia(
            local_path,
            args["path"],
            args["search"],
            args["text"],
        )
        if not success:
            logger.warning(
                f"Failed to update file {args['path']}, search phrase: {args['search']} not found or not close enough match."
            )
            return {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(
                    {
                        "error": f"Failed to update file {args['path']}, search phrase: {args['search']} not found or not close enough match."
                    }
                ),
            }

        logger.info(f"Inserted {args['text']} after {args['search']} in {args['path']}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": f"{args['path']} updated successfully.",
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
