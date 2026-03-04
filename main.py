import json
import logging
import os
import shutil
import sys
import uuid
from typing import Any, Iterable

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from git import Repo
from openai import OpenAI

from model.message import IssueComment, WebhookMessage
from utils.file import find_file, generate_top_level_file_tree, read_file
from utils.repo import (
    check_patch,
    checkout_and_apply_and_push,
    comment_on_issue,
    create_pull_request,
    prep_url,
)
from utils.search import regex_search

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
    clone_url = prep_url(issue_comment.repository.clone_url)
    repo_url = prep_url(issue_comment.repository.url)

    # clone the repo
    repo: Repo
    local_path = f"/tmp/{str(uuid.uuid4())}/{issue_comment.repository.name}"
    repo = Repo.clone_from(
        clone_url,
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

    tools: Iterable[Any] = [
        {
            "type": "function",
            "name": "search",
            "description": "Search repository using regex.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Regex pattern to use for search.",
                    },
                    "sub_path": {
                        "type": "string",
                        "description": "Optional sub-path to limit the search location relative to the repo root.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "list_files",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to repo root.",
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "read_file",
            "description": "Read a portion of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to repo root.",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Line from which to read. Cannot be < 1. Defaults to 1.",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Line at which to stop reading. Defaults to start_line + 50.",
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "submit_patch",
            "description": "Submit a code patch to resolve the issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patch": {
                        "type": "string",
                        "description": "A valid git patch to apply to the repo that implements the issue.",
                    },
                    "commit_message": {
                        "type": "string",
                        "description": "An optional commit message to add when committing the patch.",
                    },
                },
                "required": ["patch"],
                "additionalProperties": False,
            },
        },
    ]

    messages: Iterable[Any] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    logger.info(f"Sending initial message to agent: {json.dumps(messages)}")

    patch: str = ""
    commit_message: str | None = None
    calls = 0
    execute = True
    while execute:
        if calls >= 50:
            logger.warning(
                "Calls exceeded 50 iterations. Perhaps let the model know or increase the limit."
            )
            commit_message = "Agent flow exceeded 50 calls, failed to implement."
            execute = False
            break

        response = client.responses.create(
            model=os.getenv("AGENT_MODEL", "moonshotai/kimi-k2-thinking"),
            tools=tools,
            input=messages,
        )
        calls += 1

        messages.extend(response.output)

        for item in response.output:
            if item.type != "function_call":
                logger.info(f"Ingoring item in response: {item.type}")
                continue

            args: dict = json.loads(item.arguments)
            logger.info(f"Calling function: {item.name}, with args: {item.arguments}")

            if item.name == "search":
                if "query" not in args:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {
                                    "error": "query argument not given to function call search"
                                }
                            ),
                        }
                    )
                    logger.warning("query not in args for search function")
                    continue

                results = regex_search(
                    local_path,
                    args["query"],
                    args.get("sub_path", None),
                )
                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(results),
                    }
                )
                logger.info(
                    f"Returned results of search function: {json.dumps(results)}"
                )
                continue
            if item.name == "list_files":
                if "path" not in args:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {
                                    "error": "path argument not given to function call search"
                                }
                            ),
                        }
                    )
                    logger.warning("path not in args for list_files function")
                    continue

                results = generate_top_level_file_tree(local_path, args["path"])
                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(results),
                    }
                )
                logger.info(
                    f"Returned results of list files function: {json.dumps(results)}"
                )
                continue
            if item.name == "read_file":
                if "path" not in args:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {
                                    "error": "path argument not given to function call search"
                                }
                            ),
                        }
                    )
                    logger.warning("path not in args for read file function")
                    continue

                start: int = args.get("start_line", 1)
                end: int = args.get("end_line", -1)
                if end == -1:
                    end = start + 50

                if start < 1:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {
                                    "error": "start_line must be >= 1",
                                }
                            ),
                        }
                    )
                    logger.warning("start < 0 for read file functio")
                    continue
                if start >= end:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {
                                    "error": "end_line must be > than start_line",
                                }
                            ),
                        }
                    )
                    logger.warning("end not > than start for read file function")
                    continue

                try:
                    results = read_file(
                        local_path,
                        args["path"],
                        start,
                        end,
                    )
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(results),
                        }
                    )
                    logger.info(
                        f"Returned results of read file function: {json.dumps(results)}"
                    )
                except FileNotFoundError:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {
                                    "error": f"File not found with path {args['path']}",
                                }
                            ),
                        }
                    )
                    logger.warning(f"File not found with path: {args['path']}")

                continue

            if item.name == "submit_patch":
                if "patch" not in args:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {
                                    "error": "path argument not given to function call search"
                                }
                            ),
                        }
                    )
                    logger.warning("patch not in args for submit patch function")
                    continue

                # If the patch does not work or is invalid then send an error message back to the model and continue executing
                logger.info(f"Sending patch to be checked: {args['patch']}")
                ok, e = check_patch(repo, args["patch"])
                if not ok:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {
                                    "error": f"Invalid patch file. Error: {e}",
                                }
                            ),
                        }
                    )
                    logger.warning(f"Invalid patch submitted: {e}")
                    continue

                patch = args["patch"]
                commit_message = args.get("commit_message", None)
                execute = False
                logger.info("Recieved valid patch, applying and ending loop.")
                break

        # TODO: Maybe if the calls are getting close to 50 send a message to the model to say there are N calls left

    issue_branch = checkout_and_apply_and_push(
        repo,
        patch,
        issue_comment.issue.title,
        commit_message,
    )

    if not await create_pull_request(
        repo_url,
        issue_comment.repository.default_branch,
        issue_branch,
        issue_comment.issue.title,
    ):
        logger.warning("Failed to create pull request for issue.")

    # Add comments to the issue saying error or complete e.g. AGENT_RESPONSE:
    if not comment_on_issue(commit_message, clone_url):
        logger.warning("Failed to comment on issue.")

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
