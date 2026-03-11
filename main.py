import os

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from handlers.issue_handler import IssueCommentHandler
from handlers.pr_comment_handler import PRCommentHandler
from handlers.pr_review_handler import PRReviewHandler
from model.webhook_message import WebhookMessage, WebhookMessageType
from utils.logger import get_logger

load_dotenv()


logger = get_logger(__name__)

app = FastAPI(title="Webhook API", version="1.0.0")

AGENT_SECRET = os.getenv("AGENT_SECRET", None)


async def verify_webhook_auth(authorization: str | None = Header(None)):
    """
    Verify webhook authentication using a Bearer token in the Authorization header.

    To enable auth, set environment variables:
    - AGENT_SECRET=your_secret_token

    The webhook client should send the token in the 'Authorization' header as:
    Authorization: Bearer <token>
    """
    if not AGENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="AGENT_SECRET env var is not configured",
        )

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    if token != AGENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid bearer token")

    return True


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Webhook API is running",
    }


@app.post("/")
async def git_webhook_handler(
    request: Request,
    _: bool = Depends(verify_webhook_auth),
):
    """
    Webhook endpoint that accepts POST requests.

    Authorization: Bearer <your_token>
    """

    json_data = await request.json()

    message = WebhookMessage.model_validate(json_data)

    message_type, typed_message = message.infer_type()

    if message_type == WebhookMessageType.NONE or typed_message is None:
        logger.info(f"Recieved action that is not handled {message.action}")
        return JSONResponse(status_code=200, content={"status": "ok"})

    if message_type == WebhookMessageType.ISSUE_COMMENT:
        await IssueCommentHandler().handle(typed_message)
        return JSONResponse(status_code=200, content={"status": "ok"})

    if message_type == WebhookMessageType.PR_COMMENT:
        await PRCommentHandler().handle(typed_message)
        return JSONResponse(status_code=200, content={"status": "ok"})

    if message_type == WebhookMessageType.PR_REVIEW:
        await PRReviewHandler().handle(typed_message)
        return JSONResponse(status_code=200, content={"status": "ok"})

    logger.warning(f"No handler for message type {message_type}")
    return JSONResponse(status_code=200, content={"status": "ok"})


if __name__ == "__main__":
    # Load envs

    # Run the server
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting webhook server on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
