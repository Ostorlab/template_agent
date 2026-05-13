"""Unit tests for ai_model.get_vision_model."""

import pytest
from pydantic_ai.models import google, openai

from agent import ai_model


def testGetVisionModel_whenGoogleProvider_shouldReturnGoogleModel() -> None:
    model = ai_model.get_vision_model("google/gemini-2.5-pro", "fake_key")

    assert isinstance(model, google.GoogleModel)


def testGetVisionModel_whenOpenrouterProvider_shouldReturnOpenAIChatModel() -> None:
    model = ai_model.get_vision_model(
        "openrouter/meta-llama/llama-3.2-vision", "fake_key"
    )

    assert isinstance(model, openai.OpenAIChatModel)


def testGetVisionModel_whenOpenaiProvider_shouldReturnOpenAIChatModel() -> None:
    model = ai_model.get_vision_model("openai/gpt-4o", "fake_key")

    assert isinstance(model, openai.OpenAIChatModel)


def testGetVisionModel_whenUnknownProvider_shouldRaiseValueError() -> None:
    with pytest.raises(ValueError, match="No provider found"):
        ai_model.get_vision_model("unknown/some-model", "fake_key")
