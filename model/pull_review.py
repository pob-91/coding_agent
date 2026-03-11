from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PullReview(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    updated_at: datetime
    comments_count: int
