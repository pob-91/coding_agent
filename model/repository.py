from pydantic import BaseModel, ConfigDict


class Repository(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    url: str
    clone_url: str
    default_branch: str
