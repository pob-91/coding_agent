from model.pull_request import PullRequest
from model.repository import Repository
from model.review import Review
from model.webhook_message import WebhookMessage


class PRReview(WebhookMessage):
    review: Review
    repository: Repository
    pull_request: PullRequest
