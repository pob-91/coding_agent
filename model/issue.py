from pydantic import BaseModel, ConfigDict


class Issue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    title: str
    body: str
