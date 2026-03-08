from pydantic import BaseModel, ConfigDict


class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    content: str
