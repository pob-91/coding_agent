from pydantic import BaseModel, ConfigDict


class Head(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ref: str


class PullRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    url: str
    head: Head
