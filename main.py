import logging
import os
import sys

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

# Initialize logger to print to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Webhook API", version="1.0.0")

# Configuration: Set WEBHOOK_SECRET as environment variable for authentication
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", None)
WEBHOOK_AUTH_ENABLED = os.getenv("WEBHOOK_AUTH_ENABLED", "false").lower() == "true"


async def verify_webhook_auth(x_webhook_secret: str | None = Header(None)):
    """
    Verify webhook authentication using a secret token in the header.

    To enable auth, set environment variables:
    - WEBHOOK_AUTH_ENABLED=true
    - WEBHOOK_SECRET=your_secret_token

    The webhook client should send the secret in the 'X-Webhook-Secret' header.
    """
    if WEBHOOK_AUTH_ENABLED:
        if not WEBHOOK_SECRET:
            raise HTTPException(
                status_code=500,
                detail="Webhook authentication is enabled but WEBHOOK_SECRET is not configured",
            )

        if not x_webhook_secret:
            raise HTTPException(
                status_code=401, detail="Missing X-Webhook-Secret header"
            )

        if x_webhook_secret != WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

    return True


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Webhook API is running",
        "auth_enabled": WEBHOOK_AUTH_ENABLED,
    }


@app.post("/")
async def webhook_handler(
    request: Request,
    authenticated: bool = Depends(verify_webhook_auth),
):
    """
    Webhook endpoint that accepts POST requests.

    If authentication is enabled, include the X-Webhook-Secret header with your requests.
    """

    json_data = await request.json()

    if "action" not in json_data:
        logger.warning("Recieved webhook with no action")
        return

    if json_data["action"] != "created":
        logger.warning(f"Recieved action that is not handled {json_data['action']}")
        return

    if "issue" not in json_data or "comment" not in json_data:
        logger.warning(
            "Webhook body does not appear to have issue or comment info so ignoring"
        )
        return

    # TODO: Get the comment and check it is /agent COMMAND
    # Check out the code and make a branch agent/issue-number
    # How to send the correct bit of the code and context to an Agent??? Ask Chat GPT, maybe RAG it
    # Include instructions to read AGENTS.md and follow the instructions there
    # Get the patch and raise it programatically
    # Tag the MR with a correct label
    # Comment on the issue and tag it
    # Do the same again with comments on the PR to fix the pr (this time just change the branch)

    return JSONResponse(status_code=200, content={"status": "ok"})


if __name__ == "__main__":
    # Run the server
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting webhook server on {host}:{port}")
    logger.info(f"Authentication enabled: {WEBHOOK_AUTH_ENABLED}")

    uvicorn.run(app, host=host, port=port)
