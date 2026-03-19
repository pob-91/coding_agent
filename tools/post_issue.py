import json
from typing import Any, Tuple

from utils.logger import get_logger
from utils.repo import create_issue

logger = get_logger(__name__)


def post_issue(args: dict, item: Any, repo_url: str) -> Tuple[bool, dict]:
    missing_args: list[str] = []
    if "title" not in args:
        missing_args.append("title")
    if "body" not in args:
        missing_args.append("body")

    if len(missing_args) > 0:
        logger.warning(f"Missing args for post_issue: {missing_args}")
        return False, {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"the following arguments are required but missing: {missing_args}",
                }
            ),
        }

    try:
        success = create_issue(
            repo_url=repo_url,
            title=args["title"],
            body=args["body"],
        )
        if not success:
            return False, {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(
                    {
                        "error": "Failed to create the issue.",
                    }
                ),
            }

        return True, {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": f"Issue {args['title']} created successfully.",
        }
    except Exception as e:
        return False, {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Failed to create issue with error {e}",
                }
            ),
        }
