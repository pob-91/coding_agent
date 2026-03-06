from pydantic import BaseModel, ConfigDict


class PullRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: str
