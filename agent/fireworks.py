"""Fireworks AI client instantiation helper for LLM agents.

Fireworks AI exposes an OpenAI-compatible inference endpoint, so agents can use the
standard OpenAI client pointed at ``https://api.fireworks.ai/inference/v1`` with their
Fireworks API key.
"""

import os

from openai import OpenAI

FIREWORKS_API_KEY_ENV = "FIREWORKS_API_KEY"
FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"


def build_fireworks_client(
    api_key: str | None = None,
    base_url: str = FIREWORKS_BASE_URL,
) -> OpenAI:
    """Build an OpenAI client configured against the Fireworks inference endpoint.

    Args:
        api_key: Fireworks API key, defaults to the ``FIREWORKS_API_KEY`` environment
            variable.
        base_url: Fireworks inference base URL, defaults to the official endpoint.

    Returns:
        OpenAI client ready to call Fireworks-hosted models, e.g.
        ``accounts/fireworks/models/llama-v3p3-70b-instruct``.

    Raises:
        ValueError: If no API key is provided and ``FIREWORKS_API_KEY`` is not set.
    """
    resolved_api_key = (
        api_key if api_key is not None else os.environ.get(FIREWORKS_API_KEY_ENV)
    )
    if resolved_api_key is None or resolved_api_key == "":
        raise ValueError(f"{FIREWORKS_API_KEY_ENV} environment variable is not set")
    return OpenAI(api_key=resolved_api_key, base_url=base_url)
