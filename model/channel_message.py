from pydantic import ConfigDict

from model.base_db_model import BaseDBModel


class ChannelMessage(BaseDBModel):
    model_config = ConfigDict(extra="ignore")

    channel_id: str
    index: int
    body: str
