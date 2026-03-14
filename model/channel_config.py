from pydantic import ConfigDict

from model.base_db_model import BaseDBModel


class ChannelConfig(BaseDBModel):
    model_config = ConfigDict(extra="ignore")

    channel_id: str
    repo_url: str
