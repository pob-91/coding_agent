from pydantic import BaseModel, ConfigDict


class PullRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    url: str
