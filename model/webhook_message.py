from pydantic import BaseModel
from pydantic.dataclasses import dataclass


class WebhookMessageConfig:
    # Allow extra fields in the JSON that aren't in the model
    extra = "ignore"


@dataclass(config=WebhookMessageConfig)
class WebhookMessage(BaseModel):
    action: str
