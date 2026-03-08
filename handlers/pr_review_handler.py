from handlers.base_handler import BaseHandler
from model.webhook_message import WebhookMessage
from utils.logger import get_logger

logger = get_logger(__name__)


class PRReviewHandler(BaseHandler):
    async def handle(self, data: WebhookMessage) -> None:
        logger.info("PR review handler not yet implemented.")
