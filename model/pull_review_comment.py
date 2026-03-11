from pydantic import BaseModel, ConfigDict


class PullReviewComment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    body: str
    path: str
    html_url: str
    diff_hunk: str
