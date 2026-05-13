"""Unit tests for observation.observe()."""

import types
from collections.abc import Callable

import pytest_mock

from agent import models, observation


def testObserve_whenInteractFailsAndAppDead_shouldReturnDetected(
    check_context: models.CheckContext,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch("asyncio.run", return_value=None)
    mocker.patch("agent.adb_device.AdbDevice.is_process_alive", return_value=False)

    result = observation.observe("resign", check_context)

    assert result == models.CheckResult(
        "resign",
        models.TamperResult.DETECTED,
        "App died during interaction after tampering",
    )


def testObserve_whenInteractFailsAndAppAlive_shouldReturnAmbiguous(
    check_context: models.CheckContext,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch("asyncio.run", return_value=None)
    mocker.patch("agent.adb_device.AdbDevice.is_process_alive", return_value=True)

    result = observation.observe("resign", check_context)

    assert result == models.CheckResult(
        "resign",
        models.TamperResult.AMBIGUOUS,
        "monkey_tester could not interact with app (NonResponsiveApplication)",
    )


def testObserve_whenScreenshotShowsTampering_shouldReturnDetected(
    check_context: models.CheckContext,
    screenshot_zip: Callable[..., bytes],
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    zip_bytes = screenshot_zip(b"fake_png_data")
    tamper_analysis = types.SimpleNamespace(
        anti_tamper_detected=True, evidence="security warning dialog detected"
    )
    mocker.patch("asyncio.run", side_effect=[zip_bytes, tamper_analysis])

    result = observation.observe("resign", check_context)

    assert result == models.CheckResult(
        "resign",
        models.TamperResult.DETECTED,
        "security warning dialog detected",
    )


def testObserve_whenAllScreenshotsNormal_shouldReturnNotDetected(
    check_context: models.CheckContext,
    screenshot_zip: Callable[..., bytes],
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    zip_bytes = screenshot_zip(b"fake_png_1", b"fake_png_2")
    clean_analysis = types.SimpleNamespace(anti_tamper_detected=False, evidence="")
    mocker.patch("asyncio.run", side_effect=[zip_bytes, clean_analysis, clean_analysis])

    result = observation.observe("resign", check_context)

    assert result == models.CheckResult(
        "resign",
        models.TamperResult.NOT_DETECTED,
        "App ran normally — no anti-tampering response detected",
    )


def testObserve_whenZipHasNoScreenshots_shouldReturnAmbiguous(
    check_context: models.CheckContext,
    screenshot_zip: Callable[..., bytes],
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    empty_zip = screenshot_zip()
    mocker.patch("asyncio.run", return_value=empty_zip)

    result = observation.observe("resign", check_context)

    assert result == models.CheckResult(
        "resign",
        models.TamperResult.AMBIGUOUS,
        "monkey_tester returned no screenshots",
    )
