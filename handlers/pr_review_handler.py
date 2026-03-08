from flows.agent_ask import run_agent_ask
from handlers.base_handler import BaseHandler
from model.pr_review import PRReview
from model.webhook_message import WebhookMessage
from utils.logger import get_logger
from utils.repo import get_review_comments, prep_url

logger = get_logger(__name__)

_COMMAND = "/agent-ask"


class PRReviewHandler(BaseHandler):
    async def handle(self, data: WebhookMessage) -> None:
        review_event: PRReview = data  # type: ignore[assignment]

        content = review_event.review.content.strip()
        if not content.startswith(_COMMAND):
            logger.info("PR review not targeted at agents.")
            return

        question = content.removeprefix(_COMMAND).strip()
        if not question:
            logger.warning("agent-ask received empty question in PR review.")
            return

        repo_url = prep_url(review_event.repository.url)
        code_contexts = get_review_comments(
            repo_url,
            review_event.pull_request.number,
            review_event.review.id,
        )

        await run_agent_ask(
            question=question,
            repository=review_event.repository,
            pr_number=review_event.pull_request.number,
            code_contexts=code_contexts,
        )
