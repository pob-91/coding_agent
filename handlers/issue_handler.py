from flows.agent_implement import ImplementationSource, run_agent_implement
from handlers.base_handler import BaseHandler
from model.issue_comment import IssueComment
from model.webhook_message import WebhookMessage
from utils.logger import get_logger

logger = get_logger(__name__)

_COMMAND = "/agent-implement"


class IssueCommentHandler(BaseHandler):
    async def handle(self, data: WebhookMessage, workspace_id: str) -> None:
        issue_comment: IssueComment = data  # type: ignore[assignment]

        body = issue_comment.comment.body.strip()
        if not body.startswith(_COMMAND):
            logger.info("Issue comment not targeted at agents.")
            return

        agent_command = body.removeprefix(_COMMAND).strip()
        if not agent_command:
            logger.warning("agent-implement received empty command in issue comment.")
            return

        logger.info(f"Handling agent command: {agent_command}")

        await run_agent_implement(
            agent_command=agent_command,
            repository=issue_comment.repository,
            source=ImplementationSource(
                source="issue",
                issue=issue_comment.issue,
                pr=None,
            ),
            workspace_id=workspace_id,
        )
