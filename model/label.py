from pydantic import BaseModel, ConfigDict


class Label(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    id: int
