from enum import StrEnum
from typing import Tuple

from pydantic import BaseModel, ConfigDict

from model.issue_comment import IssueComment
from model.pr_comment import PRComment


class WebhookMessageType(StrEnum):
    NONE = ""
    ISSUE_COMMENT = "issue_comment"
    PR_COMMENT = "pr_comment"


class WebhookMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: str
    is_pull: bool

    def infer_type(self) -> Tuple[WebhookMessageType, "WebhookMessage | None"]:
        data = self.model_dump()
        if self.action == "created" and not self.is_pull and "pull_request" not in data:
            return WebhookMessageType.ISSUE_COMMENT, IssueComment.model_validate(data)
        if self.action == "created" and self.is_pull and "pull_request" in data:
            return WebhookMessageType.PR_COMMENT, PRComment.model_validate(data)
        return WebhookMessageType.NONE, None
