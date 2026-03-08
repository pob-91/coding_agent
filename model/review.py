from pydantic import BaseModel, ConfigDict


class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    type: str
    content: str
