from flows.agent_ask import run_agent_ask
from flows.agent_implement import ImplementationSource, PRSource, run_agent_implement
from handlers.base_handler import BaseHandler
from model.pr_comment import PRComment
from model.webhook_message import WebhookMessage
from utils.commands import ASK_COMMAND, UPDATE_COMMAND
from utils.logger import get_logger

logger = get_logger(__name__)


class PRCommentHandler(BaseHandler):
    async def handle(self, data: WebhookMessage) -> None:
        pr_comment: PRComment = data  # type: ignore[assignment]

        body = pr_comment.comment.body.strip()

        if body.startswith(ASK_COMMAND):
            question = body.removeprefix(ASK_COMMAND).strip()
            if not question:
                logger.warning("agent-ask received empty question in PR comment.")
                return

            logger.info(f"Handling agent question: {question}")

            await run_agent_ask(
                question=question,
                repository=pr_comment.repository,
                pr_number=pr_comment.pull_request.number,
                branch=pr_comment.pull_request.head.ref,
                source_comment_url=pr_comment.comment.html_url,
            )
            return

        if body.startswith(UPDATE_COMMAND):
            agent_command = body.removeprefix(UPDATE_COMMAND).strip()
            if not agent_command:
                logger.warning("agent-update received empty command in PR comment.")
                return

            logger.info(f"Handling agent command: {agent_command}")

            await run_agent_implement(
                agent_command=agent_command,
                repository=pr_comment.repository,
                source=ImplementationSource(
                    source="pr",
                    issue=None,
                    pr=PRSource(
                        pr_number=pr_comment.pull_request.number,
                        branch=pr_comment.pull_request.head.ref,
                        source_comment_url=pr_comment.comment.html_url,
                        code_contexts=None,
                    ),
                ),
            )
            return

        logger.info("PR comment not targeted at agents.")
