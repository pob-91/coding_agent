from pydantic import BaseModel
from pydantic.dataclasses import dataclass  # , Field, HttpUrl


class IssueCommentConfig:
    # Allow extra fields in the JSON that aren't in the model
    extra = "ignore"


@dataclass(config=IssueCommentConfig)
class Comment(BaseModel):
    body: str


@dataclass(config=IssueCommentConfig)
class IssueComment(BaseModel):
    comment: Comment
