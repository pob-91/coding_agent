import os
from typing import Tuple

import requests
from git import GitCommandError, Repo


def check_patch(repo: Repo, patch: str) -> Tuple[bool, str | None]:
    try:
        repo.git.apply("--check", istream=patch)
        return True, None
    except GitCommandError as e:
        return False, str(e)


def checkout_and_apply_and_push(
    repo: Repo,
    patch: str,
    issue_title: str,
    commit_message: str | None,
) -> None:
    # checkout branch
    prepped_title = issue_title.lower().replace(" ", "_")[:10]
    branch_name = f"issue/{prepped_title}"

    origin = repo.remotes.origin

    if repo.is_dirty(untracked_files=True):
        raise RuntimeError("Working tree is dirty")

    origin.fetch()

    first_push = False
    remote_refs = [ref.remote_head for ref in origin.refs]
    if branch_name in remote_refs:
        # branch exists on the remote which means this is likely an update
        repo.git.checkout("-B", branch_name, f"origin/{branch_name}")
    else:
        first_push = True
        repo.git.checkout("-b", branch_name)
        repo.git.push("-u", "origin", branch_name)

    # apply patch
    repo.git.apply("-", istream=patch)

    # stage and commit
    repo.git.add(A=True)
    repo.index.commit(commit_message or "Agent applied commit.")

    # push
    if first_push:
        repo.git.push("-u", "origin", branch_name)
    else:
        repo.git.push()


def comment_on_issue(
    agent_comment: str | None,
    issue_url: str,
) -> bool:
    comment = f"AGENT RESPONSE: {agent_comment}" or "Agent implemented the issue."

    # Issue URL ends in "/ISSUE_NUM" so we want everything apart from the issue num
    base, _ = os.path.split(issue_url)

    # And then we want to append /comments
    url = os.path.join(base, "comments")

    response = requests.post(
        url=url,
        headers={
            "Content-Type": "application/json",
        },
        json={
            "body": comment,
        },
    )

    return response.status_code == 200
