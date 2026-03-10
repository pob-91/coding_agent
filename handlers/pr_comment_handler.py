from flows.agent_ask import run_agent_ask
from handlers.base_handler import BaseHandler
from model.pr_comment import PRComment
from model.webhook_message import WebhookMessage
from utils.logger import get_logger

logger = get_logger(__name__)

_COMMAND = "/agent-ask"


class PRCommentHandler(BaseHandler):
    async def handle(self, data: WebhookMessage) -> None:
        pr_comment: PRComment = data  # type: ignore[assignment]

        body = pr_comment.comment.body.strip()
        if not body.startswith(_COMMAND):
            logger.info("PR comment not targeted at agents.")
            return

        question = body.removeprefix(_COMMAND).strip()
        if not question:
            logger.warning("agent-ask received empty question in PR comment.")
            return

        await run_agent_ask(
            question=question,
            repository=pr_comment.repository,
            comment_id=pr_comment.comment.id,
            branch=pr_comment.pull_request.head.ref,
        )
