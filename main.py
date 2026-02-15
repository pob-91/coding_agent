import json
import logging
import os
import shutil
import sys
import uuid
from collections.abc import Iterable

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from git import Repo
from openai import OpenAI
from openai.resources.chat.completions.completions import ChatCompletionToolUnionParam

from model.message import IssueComment, WebhookMessage
from utils.file import find_file, generate_top_level_file_tree

load_dotenv()

# Initialize logger to print to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Webhook API", version="1.0.0")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
)

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

    # prep the repo url
    url = issue_comment.repository.clone_url
    if url.startswith("http://"):
        url = url.removeprefix("http://")
    elif url.startswith("https://"):
        url = url.removeprefix("https://")

    url = f"https://{os.getenv('AGENT_USERNAME')}:{os.getenv('AGENT_TOKEN')}@{url}"

    # clone the repo
    repo: Repo
    local_path = f"/tmp/{str(uuid.uuid4())}/{issue_comment.repository.name}"
    repo = Repo.clone_from(
        url,
        local_path,
        depth=1,
    )

    # Ensure we are on the main branch
    try:
        repo.git.checkout("main")
    except Exception:
        pass  # Already on main branch

    # Create initial messages to send to the model
    # System prompt
    with open("./system_prompt.txt", "r") as f:
        system_prompt = f.read()

    # User prompt
    with open("./user_prompt_template.txt", "r") as f:
        user_prompt = f.read()

    user_prompt = user_prompt.replace("{{repo_name}}", issue_comment.repository.name)

    # geenrate the file tree
    file_tree = generate_top_level_file_tree(local_path)
    user_prompt = user_prompt.replace("{{file_tree}}", file_tree)

    # find and read AGENTS.md
    agents_path = find_file(local_path, "AGENTS.md")
    if agents_path is not None:
        logger.info("Found AGENTS.md, adding to user prompt.")
        with open(agents_path, "r") as f:
            agents_content = f.read()
            user_prompt = user_prompt.replace(
                "{{agents_md_content}}",
                f"START AGENTS_MD --{agents_content}-- END AGENTS_MD",
            )
    else:
        user_prompt = user_prompt.replace(
            "{{agents_md_content}}", "No AGENTS.md provided."
        )

    user_prompt = user_prompt.replace("{{issue_title}}", issue_comment.issue.title)
    user_prompt = user_prompt.replace("{{issue_body}}", issue_comment.issue.body)

    agent_command = issue_comment.comment.body.strip()
    agent_command = agent_command.removeprefix("/agent")
    agent_command = agent_command.strip()
    user_prompt = user_prompt.replace("{{agent_command}}", agent_command)

    # NOTE: If useful can either add the most recent N comments to the user prompt or pass them all to a model to summarise
    # and then add that the user prompt.
    # For now just keeping it clean and relying on the issue body.

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    logger.info(f"Sending initial message to agent: {json.dumps(messages)}")

    # calls = 0
    # while calls < 50:
    #     calls += 1

    #     completion = client.chat.completions.create(
    #         model=os.getenv("AGENT_MODEL", "x-ai/grok-code-fast-1"),
    #         messages=[
    #             {"role": "system", "content": system_prompt},
    #             {"role": "user", "content": user_prompt},
    #         ],
    #         tools=[
    #             {
    #                 "type": "function",
    #                 "function": {
    #                     "name": "search",
    #                     "description": "Search repository using regex.",
    #                     "parameters": {
    #                         "type": "object",
    #                         "properties": {
    #                             "query": {
    #                                 "type": "string",
    #                                 "description": "Regex pattern to search for",
    #                             }
    #                         },
    #                         "required": ["query"],
    #                         "additionalProperties": False,
    #                     },
    #                 },
    #             }
    #         ],
    #     )

    # TODO: See if there have been any function calls and execute them
    # Then add the response to the messages

    # If no function calls then the response must be a patch - break

    # Checkout a branch called issue/issue-num
    # Test applying the patch - if it works then apply otherwise fail the job

    # Push to the branch

    # Add comments to the issue saying error or complete e.g. AGENT_RESPONSE:

    # Delete repo
    try:
        shutil.rmtree(local_path)
    except OSError as e:
        logger.warning(f"Failed to clean up and delete repo on disk: {e.strerror}")

    return JSONResponse(status_code=200, content={"status": "ok"})


if __name__ == "__main__":
    # Load envs

    # Run the server
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting webhook server on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
