import os
import re

from ripgrepy import Ripgrepy


def regex_search(
    repo_root: str,
    regex: str,
    sub_path: str | None = None,
    result_limit: int = 20,
) -> list[dict]:
    try:
        re.compile(regex)
    except re.error as e:
        # Let the LLM know that the regex is bad
        return [
            {
                "type": "error",
                "message": "invalid regex",
                "error": str(e),
            }
        ]

    path = repo_root
    if sub_path is not None:
        path = os.path.join(path, sub_path)

    rg = Ripgrepy(regex, path)
    result: list[dict] = rg.with_filename().line_number().json().run().as_dict

    results: list[dict] = []

    for i, r in enumerate(result):
        if i >= result_limit:
            break

        full_path = r["data"]["path"]["text"]
        relative_path = os.path.relpath(full_path, repo_root)
        results.append(
            {
                "path": relative_path,
                "line": r["data"]["line_number"],
                "snippet": r["data"]["lines"]["text"],
            }
        )

    return results
