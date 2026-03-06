from model.comment import Comment
from model.issue import Issue
from model.repository import Repository
from model.webhook_message import WebhookMessage


class IssueComment(WebhookMessage):
    comment: Comment
    repository: Repository
    issue: Issue
