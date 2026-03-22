import os

from utils.logger import get_logger

logger = get_logger(__name__)


class OpenRouterHandler:
    # Public

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

    # Private

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
