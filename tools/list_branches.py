import json
from typing import Any

from git import Repo

from utils.logger import get_logger
from utils.repo import list_all_branches as lab

logger = get_logger(__name__)


def list_branches(args: dict, item: Any, repo: Repo) -> dict:
    try:
        branches = lab(repo=repo)
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": f"All available branches on the current repository: {', '.join(branches)}.",
        }
    except Exception as e:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {"error": f"Failed to checkout branch with error {e}"}
            ),
        }
