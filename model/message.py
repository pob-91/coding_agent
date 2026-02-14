from pydantic import BaseModel
from pydantic.dataclasses import dataclass


class MessageConfig:
    # Allow extra fields in the JSON that aren't in the model
    extra = "ignore"


@dataclass(config=MessageConfig)
class WebhookMessage(BaseModel):
    action: str


@dataclass(config=MessageConfig)
class Comment(BaseModel):
    body: str


@dataclass(config=MessageConfig)
class Repository(BaseModel):
    name: str
    clone_url: str


@dataclass(config=MessageConfig)
class IssueComment(BaseModel):
    comment: Comment
    repository: Repository
