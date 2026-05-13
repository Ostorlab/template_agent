"""Unit tests for AdbDevice public methods."""

import pytest
import pytest_mock

from agent import adb_device as adb_device_module


def testUploadApk_whenCalled_shouldUploadAndReturnRemotePath(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("random.randint", return_value=1234)
    mocker.patch("uuid.uuid4", return_value="test-uuid")
    upload_mock = mocker.patch("agent.device_relay.DeviceRelay.upload_file")

    result = adb_device_obj.upload_apk(b"apk_content")

    assert result == "/tmp/1234_test-uuid.apk"
    upload_mock.assert_called_once_with("/tmp/1234_test-uuid.apk", b"apk_content")


def testUninstall_whenCalled_shouldRunAdbUninstall(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    run_mock = mocker.patch(
        "agent.device_relay.DeviceRelay.run_command", return_value=(b"Success", b"")
    )

    adb_device_obj.uninstall("com.test.app")

    assert run_mock.call_args.args[0] == [
        "/usr/local/bin/adb",
        "-s",
        "emulator-5554",
        "uninstall",
        "com.test.app",
    ]


def testInstall_whenOutputContainsSuccess_shouldNotRaise(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command", return_value=(b"Success\n", b"")
    )

    adb_device_obj.install("/tmp/test.apk")


def testInstall_whenOutputLacksSuccess_shouldRaiseAdbInstallError(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command",
        return_value=(b"INSTALL_FAILED_INVALID_APK", b""),
    )

    with pytest.raises(adb_device_module.AdbInstallError):
        adb_device_obj.install("/tmp/test.apk")


def testInstall_whenFailsTwiceThenSucceeds_shouldNotRaise(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command",
        side_effect=[
            (b"INSTALL_FAILED", b""),
            (b"INSTALL_FAILED", b""),
            (b"Success\n", b""),
        ],
    )

    adb_device_obj.install("/tmp/test.apk")


def testStartApp_whenCalled_shouldRunAdbMonkey(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    run_mock = mocker.patch(
        "agent.device_relay.DeviceRelay.run_command", return_value=(b"", b"")
    )

    adb_device_obj.start_app("com.test.app")

    assert run_mock.call_args.args[0] == [
        "/usr/local/bin/adb",
        "-s",
        "emulator-5554",
        "shell",
        "monkey",
        "-p",
        "com.test.app",
        "--pct-syskeys",
        "0",
        "-c",
        "android.intent.category.LAUNCHER",
        "1",
    ]


def testIsProcessAlive_whenPackageInOutput_shouldReturnTrue(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch(
        "agent.device_relay.DeviceRelay.run_command",
        return_value=(b"u0_a99 com.test.app\n", b""),
    )

    assert adb_device_obj.is_process_alive("com.test.app") is True


def testIsProcessAlive_whenPackageNotInOutput_shouldReturnFalse(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("agent.device_relay.DeviceRelay.run_command", return_value=(b"", b""))

    assert adb_device_obj.is_process_alive("com.test.app") is False


def testRemoveRemoteFile_whenCalled_shouldRunRmCommand(
    adb_device_obj: adb_device_module.AdbDevice,
    mocker: pytest_mock.MockerFixture,
) -> None:
    run_mock = mocker.patch(
        "agent.device_relay.DeviceRelay.run_command", return_value=(b"", b"")
    )

    adb_device_obj.remove_remote_file("/tmp/test.apk")

    assert run_mock.call_args.args[0] == "rm -f /tmp/test.apk"
