"""AI model management for vision analysis."""

import logging

import httpx
from pydantic_ai import models
from pydantic_ai import settings as pydantic_ai_settings
from pydantic_ai.models import google, openai
from pydantic_ai.providers import google as google_provider
from pydantic_ai.providers import openai as openai_provider

logger = logging.getLogger(__name__)


def _get_model_settings() -> pydantic_ai_settings.ModelSettings:
    return pydantic_ai_settings.ModelSettings(timeout=250)


def _create_model(provider: str, model: str, api_key: str) -> models.Model:
    if provider in ("google", "gemini"):
        http_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout=250, connect=5))
        return google.GoogleModel(
            model_name=model,
            provider=google_provider.GoogleProvider(
                api_key=api_key, http_client=http_client
            ),
            settings=_get_model_settings(),
        )
    elif provider == "openrouter":
        return openai.OpenAIChatModel(
            model_name=model,
            provider=openai_provider.OpenAIProvider(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
            ),
            settings=_get_model_settings(),
        )
    elif provider == "openai":
        return openai.OpenAIChatModel(
            model_name=model,
            provider=openai_provider.OpenAIProvider(api_key=api_key),
            settings=_get_model_settings(),
        )
    else:
        raise ValueError(f"No provider found for {provider!r} and model {model!r}.")


def get_vision_model(model_identifier: str, api_key: str) -> models.Model:
    """Create a vision model from a provider/model identifier string."""
    provider, model = model_identifier.split("/", 1)
    return _create_model(provider, model, api_key)
