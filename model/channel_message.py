from pydantic import ConfigDict

from model.base_db_model import BaseDBModel


class ChannelMessage(BaseDBModel):
    model_config = ConfigDict(extra="ignore")

    message_id: str
    channel_id: str
    body: str
    role: str
