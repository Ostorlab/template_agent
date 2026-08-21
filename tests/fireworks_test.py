"""Unittests for the Fireworks AI client helper."""

import os
import unittest.mock

from agent import fireworks


def testBuildFireworksClient_whenApiKeyIsProvided_clientUsesFireworksEndpoint() -> None:
    """An explicit API key produces a client pointed at the Fireworks endpoint."""
    client = fireworks.build_fireworks_client(api_key="fw-explicit-key")

    assert client.api_key == "fw-explicit-key"
    assert str(client.base_url).startswith(fireworks.FIREWORKS_BASE_URL)


def testBuildFireworksClient_whenApiKeyIsNotProvided_clientUsesEnvironmentKey() -> None:
    """A missing explicit key falls back to the FIREWORKS_API_KEY environment variable."""
    with unittest.mock.patch.dict(
        os.environ, {fireworks.FIREWORKS_API_KEY_ENV: "fw-env-key"}, clear=False
    ):
        client = fireworks.build_fireworks_client()

    assert client.api_key == "fw-env-key"
    assert str(client.base_url).startswith(fireworks.FIREWORKS_BASE_URL)


def testBuildFireworksClient_whenCustomBaseUrlIsProvided_clientUsesCustomBaseUrl() -> (
    None
):
    """A custom base URL overrides the default Fireworks endpoint."""
    client = fireworks.build_fireworks_client(
        api_key="fw-explicit-key", base_url="https://custom.example.com/inference/v1"
    )

    assert str(client.base_url).startswith("https://custom.example.com/inference/v1")


def testBuildFireworksClient_whenApiKeyIsMissing_raisesValueError() -> None:
    """No explicit key and no environment key raises a ValueError."""
    with unittest.mock.patch.dict(os.environ, {}, clear=True):
        try:
            fireworks.build_fireworks_client()
        except ValueError as e:
            assert fireworks.FIREWORKS_API_KEY_ENV in str(e)
        else:
            raise AssertionError("ValueError not raised")
