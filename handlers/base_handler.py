from abc import ABC, abstractmethod

from model.webhook_message import WebhookMessage


class BaseHandler(ABC):
    @abstractmethod
    async def handle(self, data: WebhookMessage, workspace_id: str) -> None:
        pass
