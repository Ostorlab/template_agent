"""Unit tests for observation.observe()."""

import io
import types
import zipfile

import pytest
import pytest_mock

from agent import adb_device, device_relay, observation
from agent import models


def _make_screenshot_zip(*images: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i, img in enumerate(images):
            zf.writestr(f"screenshot_{i}.png", img)
    return buf.getvalue()


@pytest.fixture(name="check_context")
def fixture_check_context() -> models.CheckContext:
    relay = device_relay.DeviceRelay(
        address="127.0.0.1", port=22, username="user", password="pass"
    )
    device = adb_device.AdbDevice(device_serial="emulator-5554", device_relay=relay)
    return models.CheckContext(
        device=device,
        package_name="com.test.app",
        main_activity="com.test.app.MainActivity",
        device_version="10.0",
        vision_api_key="test_key",
        vision_model="google/gemini-test",
    )


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
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    screenshot_zip = _make_screenshot_zip(b"fake_png_data")
    tamper_analysis = types.SimpleNamespace(
        anti_tamper_detected=True, evidence="security warning dialog detected"
    )
    mocker.patch("asyncio.run", side_effect=[screenshot_zip, tamper_analysis])

    result = observation.observe("resign", check_context)

    assert result == models.CheckResult(
        "resign",
        models.TamperResult.DETECTED,
        "security warning dialog detected",
    )


def testObserve_whenAllScreenshotsNormal_shouldReturnNotDetected(
    check_context: models.CheckContext,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    screenshot_zip = _make_screenshot_zip(b"fake_png_1", b"fake_png_2")
    clean_analysis = types.SimpleNamespace(anti_tamper_detected=False, evidence="")
    mocker.patch(
        "asyncio.run", side_effect=[screenshot_zip, clean_analysis, clean_analysis]
    )

    result = observation.observe("resign", check_context)

    assert result == models.CheckResult(
        "resign",
        models.TamperResult.NOT_DETECTED,
        "App ran normally — no anti-tampering response detected",
    )


def testObserve_whenZipHasNoScreenshots_shouldReturnAmbiguous(
    check_context: models.CheckContext,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    empty_zip = _make_screenshot_zip()
    mocker.patch("asyncio.run", return_value=empty_zip)

    result = observation.observe("resign", check_context)

    assert result == models.CheckResult(
        "resign",
        models.TamperResult.AMBIGUOUS,
        "monkey_tester returned no screenshots",
    )
