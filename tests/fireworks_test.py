"""Unittests for the Fireworks AI client helper."""

import pytest
from pytest_mock import plugin

from agent import fireworks


def testBuildFireworksClient_whenApiKeyIsProvided_clientUsesFireworksEndpoint() -> None:
    """An explicit API key produces a client pointed at the Fireworks endpoint."""
    client = fireworks.build_fireworks_client(api_key="fw-explicit-key")

    assert client.api_key == "fw-explicit-key"
    assert str(client.base_url).startswith(fireworks.FIREWORKS_BASE_URL)


def testBuildFireworksClient_whenApiKeyIsNotProvided_clientUsesEnvironmentKey(
    mocker: plugin.MockerFixture,
) -> None:
    """A missing explicit key falls back to the FIREWORKS_API_KEY environment variable."""
    mocker.patch.dict(
        "os.environ", {fireworks.FIREWORKS_API_KEY_ENV: "fw-env-key"}, clear=False
    )

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


def testBuildFireworksClient_whenApiKeyIsMissing_raisesValueError(
    mocker: plugin.MockerFixture,
) -> None:
    """No explicit key and no environment key raises a ValueError."""
    mocker.patch.dict("os.environ", {}, clear=True)

    with pytest.raises(ValueError) as excinfo:
        fireworks.build_fireworks_client()

    assert fireworks.FIREWORKS_API_KEY_ENV in str(excinfo.value)
