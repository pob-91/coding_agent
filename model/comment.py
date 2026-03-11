from pydantic import BaseModel, ConfigDict


class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    body: str
    html_url: str
