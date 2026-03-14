from enum import Enum

from pydantic import BaseModel, ConfigDict


class DBModelType(Enum):
    CHANNEL_CONFIG = "CHANNEL_CONFIG"
    CHANNEL_MESSAGE = "CHANNEL_MESSAGE"


class BaseDBModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: DBModelType
