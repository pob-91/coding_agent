import json
import os
from typing import Any

from data.db_handler import DBHandler
from data.open_router import OpenRouterHandler
from model.workspace_config import WorkspaceConfig
from utils.logger import get_logger

logger = get_logger(__name__)


def get_configured_model(
    args: dict,
    item: Any,
    workspace_config: WorkspaceConfig,
) -> dict:
    missing_args: list[str] = []
    if "model_type" not in args:
        missing_args.append("model_type")

    if len(missing_args) > 0:
        logger.warning(f"Missing args for get_configured_model: {missing_args}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"the following arguments are required but missing: {missing_args}",
                }
            ),
        }

    allowed_types = {"planning", "coding", "audio"}
    if args["model_type"] not in allowed_types:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Invalid model type: {args['model_type']} expected one of {allowed_types}",
                }
            ),
        }

    model: str = ""
    if args["model_type"] == "planning":
        model = OpenRouterHandler.get_planning_model(
            configured_model=workspace_config.planning_model,
        )
    elif args["model_type"] == "coding":
        model = OpenRouterHandler.get_planning_model(
            configured_model=workspace_config.agent_model,
        )
    elif args["model_type"] == "audio":
        model = OpenRouterHandler.get_planning_model(
            configured_model=workspace_config.audio_model,
        )

    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": f"Currently configured model for {args['model_type']} is {model}",
    }


def list_available_models(args: dict, item: Any) -> dict:
    missing_args: list[str] = []
    if "model_type" not in args:
        missing_args.append("model_type")

    if len(missing_args) > 0:
        logger.warning(f"Missing args for get_configured_model: {missing_args}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"the following arguments are required but missing: {missing_args}",
                }
            ),
        }

    allowed_types = {"planning", "coding", "audio"}
    if args["model_type"] not in allowed_types:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Invalid model type: {args['model_type']} expected one of {allowed_types}",
                }
            ),
        }

    models: list[str] = []
    if args["model_type"] == "planning":
        models = os.getenv("PLANNING_MODELS", "").split(",")
    elif args["model_type"] == "coding":
        models = os.getenv("AGENT_MODELS", "").split(",")
    elif args["model_type"] == "audio":
        models = os.getenv("AUDIO_MODELS", "").split(",")

    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": f"All available models for {args['model_type']} are {models}",
    }


def configure_model(
    args: dict,
    item: Any,
    workspace_config: WorkspaceConfig,
) -> dict:
    missing_args: list[str] = []
    if "model_type" not in args:
        missing_args.append("model_type")
    if "model_name" not in args:
        missing_args.append("model_name")

    if len(missing_args) > 0:
        logger.warning(f"Missing args for get_configured_model: {missing_args}")
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"the following arguments are required but missing: {missing_args}",
                }
            ),
        }

    allowed_types = {"planning", "coding", "audio"}
    if args["model_type"] not in allowed_types:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Invalid model type: {args['model_type']} expected one of {allowed_types}",
                }
            ),
        }

    models: list[str] = []
    if args["model_type"] == "planning":
        models = os.getenv("PLANNING_MODELS", "").split(",")
    elif args["model_type"] == "coding":
        models = os.getenv("AGENT_MODELS", "").split(",")
    elif args["model_type"] == "audio":
        models = os.getenv("AUDIO_MODELS", "").split(",")

    if args["model_name"] not in models:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Invalid model name: {args['model_name']} not one of the available models for {args['model_type']}. Use the list_available_models tool to discover available models.",
                }
            ),
        }

    config = WorkspaceConfig(
        **workspace_config.model_dump(mode="json"),
    )

    if args["model_type"] == "planning":
        config.planning_model = args["model_name"]
    elif args["model_type"] == "coding":
        config.agent_model = args["model_name"]
    elif args["model_type"] == "audio":
        config.audio_model = args["model_name"]

    try:
        DBHandler.update_model(config)
    except Exception as e:
        return {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(
                {
                    "error": f"Failed to update the model config with error: {e}",
                }
            ),
        }

    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": "Successfully updated the model config.",
    }
