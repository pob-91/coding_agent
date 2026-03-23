import os
import time
from typing import Any

import requests

from model.model_info import ModelInfo, Pricing, TopProvider
from utils.logger import get_logger

logger = get_logger(__name__)


class OpenRouterHandler:
    # Public
    _models_cache: dict[str, ModelInfo] = {}
    _cache_timestamp: float | None = None
    CACHE_TTL_SECONDS = 3600


    @staticmethod
    def get_planning_model(configured_model: str | None = None) -> str:
        return OpenRouterHandler._get_model(
            model_name=configured_model, key="PLANNING_MODELS"
        )

    @staticmethod
    def get_agent_model(configured_model: str | None = None) -> str:
        return OpenRouterHandler._get_model(
            model_name=configured_model, key="AGENT_MODELS"
        )

    @staticmethod
    def get_audio_model(configured_model: str | None = None) -> str:
        return OpenRouterHandler._get_model(
            model_name=configured_model, key="AUDIO_MODELS"
        )

    @staticmethod
    def get_model_info(model_id: str) -> ModelInfo | None:
        if OpenRouterHandler._cache_timestamp is None:
            OpenRouterHandler._refresh_models_cache()
        elif time.time() - OpenRouterHandler._cache_timestamp > OpenRouterHandler.CACHE_TTL_SECONDS:
            OpenRouterHandler._refresh_models_cache()

        return OpenRouterHandler._models_cache.get(model_id)

    # Private

    @staticmethod
    def _refresh_models_cache() -> None:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=30)
        response.raise_for_status()

        payload: dict[str, Any] = response.json()
        models = payload.get("data", [])

        cache: dict[str, ModelInfo] = {}
        for model in models:
            top_provider = model.get("top_provider")
            pricing_data = model.get("pricing")
            cache[model["id"]] = ModelInfo(
                id=model["id"],
                name=model.get("name"),
                description=model.get("description"),
                pricing=Pricing(
                    prompt=pricing_data.get("prompt"),
                    completion=pricing_data.get("completion"),
                )
                if isinstance(pricing_data, dict)
                else None,
                context_length=model.get("context_length"),
                supported_parameters=model.get("supported_parameters", []),
                top_provider=TopProvider(
                    context_length=top_provider.get("context_length"),
                    max_completion_tokens=top_provider.get("max_completion_tokens"),
                    is_moderated=top_provider.get("is_moderated"),
                )
                if isinstance(top_provider, dict)
                else None,
                input_modalities=model.get("input_modalities", []),
                output_modalities=model.get("output_modalities", []),
            )

        OpenRouterHandler._models_cache = cache
        OpenRouterHandler._cache_timestamp = time.time()

    @staticmethod
    def _get_model(model_name: str | None, key: str) -> str:
        models = os.getenv(key, "").split(",")
        if len(models) == 0:
            logger.warning(f"No models found for {key}. Returning default.")
            return "google/gemini-2.5-flash"

        if model_name is None:
            return models[0]

        if model_name not in models:
            return models[0]

        return model_name
