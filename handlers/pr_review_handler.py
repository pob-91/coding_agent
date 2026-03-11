from flows.agent_ask import run_agent_ask
from handlers.base_handler import BaseHandler
from model.pr_review import PRReview
from model.webhook_message import WebhookMessage
from utils.logger import get_logger
from utils.repo import get_most_recent_review_comments, prep_url

logger = get_logger(__name__)

_COMMAND = "/agent-ask"


class PRReviewHandler(BaseHandler):
    async def handle(self, data: WebhookMessage) -> None:
        review_event: PRReview = data  # type: ignore[assignment]

        repo_url = prep_url(review_event.repository.url)
        all_comments = get_most_recent_review_comments(
            repo_url,
            review_event.pull_request.number,
        )

        triggering_comments = [
            c for c in all_comments if c.body.strip().startswith(_COMMAND)
        ]

        if len(triggering_comments) == 0:
            logger.info("PR review not targeted at agents.")
            return

        for triggering_comment in triggering_comments:
            question = triggering_comment.body.strip().removeprefix(_COMMAND).strip()
            if not question:
                logger.warning("agent-ask received empty question in PR review.")
                continue

            await run_agent_ask(
                question=question,
                repository=review_event.repository,
                pr_number=review_event.pull_request.number,
                branch=review_event.pull_request.head.ref,
                code_contexts=[triggering_comment],
                source_comment_url=triggering_comment.html_url,
            )
