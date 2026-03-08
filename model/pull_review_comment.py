from pydantic import BaseModel, ConfigDict


class PullReviewComment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    body: str
    path: str
    diff_hunk: str
    position: int
    original_position: int
    commit_id: str
    original_commit_id: str
    pull_request_review_id: int
