import json
from typing import Any

from git import Repo

from utils.logger import get_logger
from utils.repo import checkout_branch as cb

logger = get_logger(__name__)


def checkout_branch(args: dict, item: Any, repo: Repo) -> dict:
    if "branch_name" not in args:
        logger.warning("Missing branch_name arg for checkout_branch")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"error": "branch_name argument is required"}),
        }

    try:
        cb(
            repo=repo,
            branch_name=args["branch_name"],
        )
    except Exception as e:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {"error": f"Failed to checkout branch with error {e}"}
            ),
        }

    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": f"Branch {args['branch_name']} checked out successfully.",
    }
