import os
from typing import Tuple

import requests
from git import Repo

from model.label import Label


def prep_url(raw: str) -> str:
    if raw.startswith("http://"):
        raw = raw.removeprefix("http://")
    elif raw.startswith("https://"):
        raw = raw.removeprefix("https://")

    return f"https://{os.getenv('AGENT_USERNAME')}:{os.getenv('AGENT_TOKEN')}@{raw}"


def checkout_issue_branch(repo: Repo, issue_title: str) -> Tuple[str, bool]:
    # checkout branch
    prepped_title = issue_title.lower().replace(" ", "_")
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

    return branch_name, first_push


def commit_changes_and_push(
    repo: Repo,
    branch_name: str,
    first_push: bool,
    commit_message: str | None,
) -> None:
    # commit changes
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
    comment = f"AGENT RESPONSE: {agent_comment}" if agent_comment else "Agent implemented the issue."
    # And then we want to append /comments
    url = os.path.join(issue_url, "comments")

    response = requests.post(
        url=url,
        headers={
            "Content-Type": "application/json",
        },
        json={
            "body": comment,
        },
    )

    return response.status_code == 201


async def create_pull_request(
    repo_url: str,
    base_branch: str,
    issue_branch: str,
    issue_title: str,
) -> bool:
    # https://git.thesanders.farm/api/v1/repos/nerd/coding_agent
    url = os.path.join(repo_url, "pulls")

    # Get the label to use
    label_id = await _get_ai_agent_label(repo_url)

    response = requests.post(
        url=url,
        headers={
            "Content-Type": "application/json",
        },
        json={
            "base": base_branch,
            "head": issue_branch,  # The PR branch
            "title": issue_title,
            "labels": [
                label_id,
            ]
            if label_id is not None
            else [],
        },
    )

    return response.status_code == 201


async def _get_ai_agent_label(repo_url: str) -> int | None:
    labels_url = os.path.join(repo_url, "labels")

    labels_response = requests.get(
        url=labels_url,
    )
    if labels_response.status_code != 200:
        return None

    json_data: list = labels_response.json()
    for d in json_data:
        label = Label.model_validate(d)
        if label.name == "Coding Agent":
            return label.id

    # No existing label, need to create one
    create_label_response = requests.post(
        url=labels_url,
        headers={
            "Content-Type": "application/json",
        },
        json={
            "color": "#507dbc",
            "name": "Coding Agent",
        },
    )

    if create_label_response.status_code != 201:
        return None

    label_data = create_label_response.json()
    label = Label.model_validate(label_data)

    return label.id
