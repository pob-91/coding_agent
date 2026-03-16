import os
import uuid
from dataclasses import dataclass

import requests
from git import Repo

from model.label import Label
from model.pull_review import PullReview
from model.pull_review_comment import PullReviewComment
from utils.logger import get_logger

logger = get_logger(__name__)


def prep_url(raw: str) -> str:
    if raw.startswith("http://"):
        raw = raw.removeprefix("http://")
    elif raw.startswith("https://"):
        raw = raw.removeprefix("https://")

    return f"https://{os.getenv('AGENT_USERNAME')}:{os.getenv('AGENT_TOKEN')}@{raw}"


def prep_issue_branch_name(issue_title: str) -> str:
    prepped_title = issue_title.lower().replace(" ", "_")
    return f"issue/{prepped_title}"


@dataclass
class CheckoutResponse:
    repo: Repo
    branch_name: str
    first_push: bool
    local_path: str


def clone_and_checkout(
    repo_name: str,
    clone_url: str,
    branch_name: str | None = None,
    is_planning_agent: bool = False,
) -> CheckoutResponse:
    if is_planning_agent:
        local_path = f"/tmp/planning_agent/{repo_name}"
    else:
        local_path = f"/tmp/{uuid.uuid4()}/{repo_name}"

    # If repo already exists, fetch and return early for planning agent
    if os.path.exists(local_path):
        repo = Repo(local_path)
        current_branch = repo.active_branch.name
        local_commit = repo.head.commit.hexsha

        repo.git.fetch("-p")

        if is_planning_agent:
            remote_commit = repo.remotes.origin.refs[current_branch].commit.hexsha
            if local_commit != remote_commit:
                repo.git.pull("origin", current_branch)

        return CheckoutResponse(
            repo=repo,
            branch_name=current_branch,
            first_push=False,
            local_path=local_path,
        )

    repo = Repo.clone_from(clone_url, local_path, depth=1)

    origin = repo.remotes.origin

    if repo.is_dirty(untracked_files=True):
        raise RuntimeError("Working tree is dirty")

    # The checkout depth is 1 so we need to update the origin to track all branches
    repo.git.remote("set-branches", "origin", "*")
    repo.git.fetch("origin", "--depth=1")

    first_push = False

    if branch_name is not None:
        remote_refs = [ref.remote_head for ref in origin.refs]
        if branch_name in remote_refs:
            # branch exists on the remote which means this is likely an update
            repo.git.checkout("-B", branch_name, f"origin/{branch_name}")
        else:
            first_push = True
            repo.git.checkout("-b", branch_name)

    return CheckoutResponse(
        repo=repo,
        branch_name=repo.active_branch.name,
        first_push=first_push,
        local_path=local_path,
    )


def list_all_branches(repo: Repo) -> list[str]:
    local = [branch.name for branch in repo.branches]
    remote = [ref.remote_head for ref in repo.remotes.origin.refs]

    # Combine and remove duplicates
    return list(set(local + remote))


def checkout_branch(repo: Repo, branch_name: str) -> None:
    current_branch = repo.active_branch.name

    if current_branch != branch_name:
        repo.git.checkout("-B", branch_name, f"origin/{branch_name}")

    repo.git.fetch("-p")

    local_commit = repo.head.commit.hexsha
    remote_commit = repo.remotes.origin.refs[current_branch].commit.hexsha

    if local_commit != remote_commit:
        repo.git.pull("origin", current_branch)


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
    comment = (
        f"AGENT RESPONSE: {agent_comment}"
        if agent_comment
        else "Agent implemented the issue."
    )
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


def post_on_pr(
    agent_comment: str,
    repo_url: str,
    pr_number: int,
    source_comment_url: str | None = None,
) -> bool:
    if source_comment_url is None:
        comment = f"AGENT RESPONSE:\n\n {agent_comment}"
    else:
        comment = f"AGENT RESPONSE [source comment]({source_comment_url}):\n\n {agent_comment}"

    url = os.path.join(repo_url, "issues", str(pr_number), "comments")

    response = requests.post(
        url=url,
        headers={"Content-Type": "application/json"},
        json={"body": comment},
    )

    if response.status_code != 201:
        logger.error(f"Failed to comment on PR with code {response.status_code}")

    return response.status_code == 201


def get_most_recent_review_comments(
    repo_url: str,
    pr_number: int,
) -> list[PullReviewComment]:
    reviews_url = os.path.join(repo_url, "pulls", str(pr_number), "reviews")
    reviews_response = requests.get(url=reviews_url)
    if reviews_response.status_code != 200:
        logger.error(
            f"Failed to get reviews on pull request: {reviews_response.status_code}"
        )
        return []

    reviews = [PullReview.model_validate(r) for r in reviews_response.json()]
    reviews = [r for r in reviews if r.comments_count > 0]
    reviews = sorted(reviews, key=lambda x: x.updated_at, reverse=True)

    recent_comments_url = os.path.join(
        repo_url, "pulls", str(pr_number), "reviews", str(reviews[0].id), "comments"
    )

    response = requests.get(url=recent_comments_url)

    if response.status_code != 200:
        logger.error(f"Failed to get comments on review: {response.status_code}")
        return []

    return [PullReviewComment.model_validate(c) for c in response.json()]


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
