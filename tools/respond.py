import json
from typing import Any

from utils.logger import get_logger
from utils.repo import post_on_pr

logger = get_logger(__name__)


def respond(
    args: dict,
    item: Any,
    repo_url: str,
    pr_number: int,
    source_comment_url: str | None = None,
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

    posted = post_on_pr(
        args["answer"],
        repo_url,
        pr_number,
        source_comment_url,
    )
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
