from model.pull_request import PullRequest
from model.repository import Repository
from model.webhook_message import WebhookMessage


class PRReview(WebhookMessage):
    repository: Repository
    pull_request: PullRequest
