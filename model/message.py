from pydantic import BaseModel, ConfigDict


class WebhookMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: str


class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    body: str


class Repository(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    url: str
    clone_url: str
    default_branch: str


class Issue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    body: str


class IssueComment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    comment: Comment
    repository: Repository
    issue: Issue
