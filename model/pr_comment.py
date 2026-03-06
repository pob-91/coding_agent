from model.comment import Comment
from model.pull_request import PullRequest
from model.repository import Repository
from model.webhook_message import WebhookMessage


class PRComment(WebhookMessage):
    comment: Comment
    repository: Repository
    pull_request: PullRequest
