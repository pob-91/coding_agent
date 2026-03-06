from pydantic import BaseModel, ConfigDict


class Issue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    body: str
