"""Unit tests for AntiTamperingAgent."""

import pytest_mock
from ostorlab.agent.message import message

from agent import anti_tampering_agent


def testAntiTamperingAgent_whenApkAndBaselineOk_shouldCompleteWithNoVulnerabilities(
    tampering_agent: anti_tampering_agent.AntiTamperingAgent,
    fake_apk_message: message.Message,
    agent_mock: list[message.Message],
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch("time.sleep")
    mock_apk = mocker.patch("androguard.core.apk.APK")
    mock_apk.return_value.get_package.return_value = "com.test.app"
    mock_apk.return_value.get_main_activities.return_value = [
        "com.test.app.MainActivity"
    ]
    mocker.patch("agent.device_relay.DeviceRelay.upload_file")
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command",
        side_effect=[
            (b"", b""),  # uninstall (pre-install)
            (b"Success\n", b""),  # install
            (b"", b""),  # rm -f remote apk
            (b"", b""),  # start_app
            (b"u0_a99 com.test.app", b""),  # is_process_alive → True
            (b"", b""),  # uninstall (end of baseline)
            (b"", b""),  # uninstall (finally cleanup)
        ],
    )

    tampering_agent.process(fake_apk_message)

    assert agent_mock == []


def testAntiTamperingAgent_whenBaselineCrashes_shouldSkipChecks(
    tampering_agent: anti_tampering_agent.AntiTamperingAgent,
    fake_apk_message: message.Message,
    agent_mock: list[message.Message],
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch("time.sleep")
    mock_apk = mocker.patch("androguard.core.apk.APK")
    mock_apk.return_value.get_package.return_value = "com.test.app"
    mock_apk.return_value.get_main_activities.return_value = [
        "com.test.app.MainActivity"
    ]
    mocker.patch("agent.device_relay.DeviceRelay.upload_file")
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command",
        side_effect=[
            (b"", b""),  # uninstall
            (b"Success\n", b""),  # install
            (b"", b""),  # rm -f remote apk
            (b"", b""),  # start_app
            (b"", b""),  # is_process_alive → False (pkg not in stdout)
            (b"", b""),  # uninstall (end of baseline)
        ],
    )
    observe_mock = mocker.patch("agent.observation.observe")

    tampering_agent.process(fake_apk_message)

    assert agent_mock == []
    assert observe_mock.called is False


def testAntiTamperingAgent_whenInstallFails_shouldSkipChecks(
    tampering_agent: anti_tampering_agent.AntiTamperingAgent,
    fake_apk_message: message.Message,
    agent_mock: list[message.Message],
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch("time.sleep")
    mock_apk = mocker.patch("androguard.core.apk.APK")
    mock_apk.return_value.get_package.return_value = "com.test.app"
    mock_apk.return_value.get_main_activities.return_value = [
        "com.test.app.MainActivity"
    ]
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
    observe_mock = mocker.patch("agent.observation.observe")

    tampering_agent.process(fake_apk_message)

    assert agent_mock == []
    assert observe_mock.called is False


def testAntiTamperingAgent_whenNoApkContent_shouldReturnEarly(
    tampering_agent: anti_tampering_agent.AntiTamperingAgent,
    agent_mock: list[message.Message],
    mocker: pytest_mock.MockerFixture,
) -> None:
    empty_message = message.Message.from_data(
        "v3.asset.file.android.apk",
        data={"path": "test.apk"},
    )
    run_command_mock = mocker.patch("agent.device_relay.DeviceRelay.run_command")

    tampering_agent.process(empty_message)

    assert agent_mock == []
    assert run_command_mock.called is False


def testAntiTamperingAgent_whenUnexpectedSelector_shouldNotProcess(
    tampering_agent: anti_tampering_agent.AntiTamperingAgent,
    agent_mock: list[message.Message],
    mocker: pytest_mock.MockerFixture,
) -> None:
    unknown_message = message.Message.from_data(
        "v3.asset.file.android.apk",
        data={"content": b"data", "path": "test.apk"},
    )
    unknown_message.selector = "v3.asset.file.unknown"
    run_command_mock = mocker.patch("agent.device_relay.DeviceRelay.run_command")

    tampering_agent.process(unknown_message)

    assert agent_mock == []
    assert run_command_mock.called is False
