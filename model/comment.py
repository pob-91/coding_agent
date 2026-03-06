from pydantic import BaseModel, ConfigDict


class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    body: str
