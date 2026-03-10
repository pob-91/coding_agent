import json
from typing import Any

from utils.logger import get_logger
from utils.repo import reply_to_comment

logger = get_logger(__name__)


def respond(
    args: dict,
    item: Any,
    comment_id: int,
    repo_url: str,
) -> dict:
    missing_args: list[str] = []
    if "answer" not in args:
        missing_args.append("answer")

    if len(missing_args) > 0:
        logger.warning(f"Missing args for respond: {missing_args}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"the following arguments are required but missing: {missing_args}",
                }
            ),
        }

    posted = reply_to_comment(args["answer"], repo_url, comment_id)
    if not posted:
        logger.warning("agent-ask failed to post answer as comment.")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": "Failed to post answer as comment.",
                }
            ),
        }

    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": "Answer posted",
    }
