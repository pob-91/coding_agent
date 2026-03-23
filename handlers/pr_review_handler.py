from flows.agent_ask import run_agent_ask
from flows.agent_implement import ImplementationSource, PRSource, run_agent_implement
from handlers.base_handler import BaseHandler
from model.pr_review import PRReview
from model.webhook_message import WebhookMessage
from utils.commands import ASK_COMMAND, UPDATE_COMMAND
from utils.logger import get_logger
from utils.repo import get_most_recent_review_comments, prep_url

logger = get_logger(__name__)


class PRReviewHandler(BaseHandler):
    async def handle(self, data: WebhookMessage, workspace_id: str) -> None:
        review_event: PRReview = data  # type: ignore[assignment]

        repo_url = prep_url(review_event.repository.url)
        all_comments = get_most_recent_review_comments(
            repo_url,
            review_event.pull_request.number,
        )

        ask_comments = [
            c for c in all_comments if c.body.strip().startswith(ASK_COMMAND)
        ]
        update_comments = [
            c for c in all_comments if c.body.strip().startswith(UPDATE_COMMAND)
        ]

        if len(ask_comments) == 0 and len(update_comments) == 0:
            logger.info("PR review not targeted at agents.")
            return

        for ask_comment in ask_comments:
            question = ask_comment.body.strip().removeprefix(ASK_COMMAND).strip()
            if not question:
                logger.warning("agent-ask received empty question in PR review.")
                continue

            await run_agent_ask(
                question=question,
                repository=review_event.repository,
                pr_number=review_event.pull_request.number,
                branch=review_event.pull_request.head.ref,
                code_contexts=[ask_comment],
                source_comment_url=ask_comment.html_url,
                workspace_id=workspace_id,
            )

        for update_comment in update_comments:
            agent_command = update_comment.body.removeprefix(UPDATE_COMMAND).strip()
            if not agent_command:
                logger.warning("agent-update received empty command in PR review.")
                return

            logger.info(f"Handling agent command: {agent_command}")

            await run_agent_implement(
                agent_command=agent_command,
                repository=review_event.repository,
                source=ImplementationSource(
                    source="pr",
                    issue=None,
                    pr=PRSource(
                        pr_number=review_event.pull_request.number,
                        branch=review_event.pull_request.head.ref,
                        source_comment_url=update_comment.html_url,
                        code_contexts=[update_comment],
                    ),
                ),
                workspace_id=workspace_id,
            )
