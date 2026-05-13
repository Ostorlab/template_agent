"""Unit tests for DeviceRelay public methods."""

import pytest_mock
from paramiko import ssh_exception

from agent import device_relay as device_relay_module


def testRunCommand_whenPassedAsList_shouldJoinAndExecute(
    relay: device_relay_module.DeviceRelay,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mock_ssh_cls = mocker.patch("paramiko.client.SSHClient")
    mock_ssh = mock_ssh_cls.return_value
    mock_ssh.get_transport.return_value = mocker.MagicMock()
    mock_stdout = mocker.MagicMock()
    mock_stdout.read.return_value = b"output"
    mock_stderr = mocker.MagicMock()
    mock_stderr.read.return_value = b""
    mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)

    stdout, stderr = relay.run_command(["adb", "-s", "emulator-5554", "shell", "ps"])

    assert (
        mock_ssh.exec_command.call_args.kwargs["command"]
        == "adb -s emulator-5554 shell ps"
    )
    assert stdout == b"output"
    assert stderr == b""


def testRunCommand_whenPassedAString_shouldExecuteDirectly(
    relay: device_relay_module.DeviceRelay,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mock_ssh_cls = mocker.patch("paramiko.client.SSHClient")
    mock_ssh = mock_ssh_cls.return_value
    mock_ssh.get_transport.return_value = mocker.MagicMock()
    mock_stdout = mocker.MagicMock()
    mock_stdout.read.return_value = b"output"
    mock_stderr = mocker.MagicMock()
    mock_stderr.read.return_value = b""
    mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)

    stdout, stderr = relay.run_command("rm -f /tmp/test.apk")

    assert mock_ssh.exec_command.call_args.kwargs["command"] == "rm -f /tmp/test.apk"
    assert stdout == b"output"
    assert stderr == b""


def testRunCommand_whenSshExceptionOnFirstAttempt_shouldRetryAndSucceed(
    relay: device_relay_module.DeviceRelay,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mock_ssh_cls = mocker.patch("paramiko.client.SSHClient")
    mock_stdout = mocker.MagicMock()
    mock_stdout.read.return_value = b"ok"
    mock_stderr = mocker.MagicMock()
    mock_stderr.read.return_value = b""

    fail_instance = mocker.MagicMock()
    fail_instance.get_transport.side_effect = ssh_exception.SSHException(
        "connection failed"
    )

    success_instance = mocker.MagicMock()
    success_instance.get_transport.return_value = mocker.MagicMock()
    success_instance.exec_command.return_value = (None, mock_stdout, mock_stderr)

    mock_ssh_cls.side_effect = [fail_instance, success_instance]

    stdout, _ = relay.run_command("echo hello")

    assert stdout == b"ok"


def testUploadFile_whenCalled_shouldSftpPutToRemotePath(
    relay: device_relay_module.DeviceRelay,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch("tenacity.nap.sleep")
    mock_transport_cls = mocker.patch("paramiko.Transport")
    mock_transport = mock_transport_cls.return_value
    mock_sftp = mocker.MagicMock()
    mock_sftp.get_channel.return_value = mocker.MagicMock()
    mocker.patch("paramiko.SFTPClient.from_transport", return_value=mock_sftp)

    relay.upload_file("/remote/path/test.apk", b"apk_content")

    assert mock_sftp.put.call_args.args[1] == "/remote/path/test.apk"
    assert mock_transport.connect.called is True
    assert mock_sftp.close.called is True
    assert mock_transport.close.called is True
