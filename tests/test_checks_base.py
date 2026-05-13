"""Unit tests for TamperCheck.run() template method."""

import pytest_mock

from agent import models
from agent.checks import base


class _PassthroughCheck(base.TamperCheck):
    name = "test_check"
    kb_missing = None  # type: ignore[assignment]
    kb_detected = None  # type: ignore[assignment]

    def apply(self, content: bytes) -> bytes:
        return content + b"_tampered"


def testTamperCheckRun_whenInstallSucceedsAndAppAlive_shouldReturnObserveResult(
    check_context: models.CheckContext,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch("time.sleep")
    mocker.patch("agent.device_relay.DeviceRelay.upload_file")
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command",
        side_effect=[
            (b"", b""),  # uninstall
            (b"Success\n", b""),  # install
            (b"", b""),  # rm -f remote apk
            (b"", b""),  # start_app
            (b"u0_a99 com.test.app", b""),  # is_process_alive → True
        ],
    )
    expected = models.CheckResult(
        "test_check", models.TamperResult.NOT_DETECTED, "all good"
    )
    mocker.patch("agent.observation.observe", return_value=expected)

    result = _PassthroughCheck().run(b"apk_content", check_context)

    assert result == models.CheckResult(
        "test_check", models.TamperResult.NOT_DETECTED, "all good"
    )


def testTamperCheckRun_whenInstallFails_shouldReturnAmbiguous(
    check_context: models.CheckContext,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch("time.sleep")
    mocker.patch("agent.device_relay.DeviceRelay.upload_file")
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command",
        side_effect=[
            (b"", b""),  # uninstall
            (b"INSTALL_FAILED_INVALID_APK", b""),  # install attempt 1
            (b"INSTALL_FAILED_INVALID_APK", b""),  # install attempt 2
            (b"INSTALL_FAILED_INVALID_APK", b""),  # install attempt 3 → AdbInstallError
            (b"", b""),  # rm -f remote apk (finally)
        ],
    )

    result = _PassthroughCheck().run(b"apk_content", check_context)

    assert result.result == models.TamperResult.AMBIGUOUS
    assert "Install failed" in result.evidence


def testTamperCheckRun_whenAppDiesAtStartup_shouldReturnDetected(
    check_context: models.CheckContext,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch("time.sleep")
    mocker.patch("agent.device_relay.DeviceRelay.upload_file")
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command",
        side_effect=[
            (b"", b""),  # uninstall
            (b"Success\n", b""),  # install
            (b"", b""),  # rm -f remote apk
            (b"", b""),  # start_app
            (b"", b""),  # is_process_alive → False
        ],
    )

    result = _PassthroughCheck().run(b"apk_content", check_context)

    assert result == models.CheckResult(
        "test_check",
        models.TamperResult.DETECTED,
        "App died at startup after tampering",
    )
