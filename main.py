import json
import logging
import os
import sys

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from model.issue_comment import IssueComment
from model.webhook_message import WebhookMessage

load_dotenv()

# Initialize logger to print to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

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
async def webhook_handler(
    request: Request,
    _: bool = Depends(verify_webhook_auth),
):
    """
    Webhook endpoint that accepts POST requests.

    Authorization: Bearer <your_token>
    """

    json_data = await request.json()

    message = WebhookMessage.model_validate(json_data)

    # TODO: Extend this to handle pull request comments to update existing MRs
    if message.action != "created":
        logger.warning(f"Recieved action that is not handled {message.action}")
        return

    issue_comment = IssueComment.model_validate(json_data)

    comment = issue_comment.comment.body.strip()
    if not comment.startswith("/agent"):
        logger.info("Issue comment not targeted at agents.")
        return

    command = comment.removeprefix("/agent")

    logger.info(f"Handling agent command: {command}")

    # Checkout FLOW.md for info on how this works

    return JSONResponse(status_code=200, content={"status": "ok"})


if __name__ == "__main__":
    # Load envs

    # Run the server
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting webhook server on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
