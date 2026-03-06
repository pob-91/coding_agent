from abc import ABC, abstractmethod
from typing import Any


class BaseHandler(ABC):
    @abstractmethod
    async def handle(self, data: Any) -> None:
        pass
