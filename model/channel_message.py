from typing import Literal

from pydantic import ConfigDict

from model.base_db_model import BaseDBModel


class ChannelMessage(BaseDBModel):
    model_config = ConfigDict(extra="ignore")

    message_id: str
    channel_id: str
    body: str
    role: Literal["user", "assistant", "tool_call", "tool_output"]
    call_id: str | None = None
    tool_name: str | None = None
