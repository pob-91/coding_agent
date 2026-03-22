from pydantic import ConfigDict

from model.base_db_model import BaseDBModel


class WorkspaceConfig(BaseDBModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    bot_user_id: str
    team_id: str

    planning_model: str | None = None
    agent_model: str | None = None
    audio_model: str | None = None
