from pydantic import BaseModel, ConfigDict


class WebhookMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: str
    is_pull: bool
