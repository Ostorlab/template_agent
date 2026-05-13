"""SSH relay: run commands and upload files on a remote machine."""

import datetime
import logging
import tempfile
from collections.abc import Sequence
from typing import Optional

import paramiko
from paramiko import client as paramiko_client
from paramiko import ssh_exception
import tenacity

logger = logging.getLogger(__name__)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
logging.getLogger("paramiko.sftp").setLevel(logging.WARNING)

DEFAULT_KEEPALIVE = 10
MAX_SSH_TRIES = 4
INTERVAL_BETWEEN_SSH = datetime.timedelta(seconds=0.5)
DEFAULT_UPLOAD_TIMEOUT = 120


class DeviceRelay:
    """SSH relay: run commands and upload files on a remote machine."""

    def __init__(
        self,
        address: str,
        port: int = 22,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.address = address
        self.port = port
        self.username = username
        self.password = password

    @tenacity.retry(
        stop=tenacity.stop.stop_after_attempt(MAX_SSH_TRIES),
        retry=tenacity.retry_if_exception_type(ssh_exception.SSHException),
        wait=tenacity.wait.wait_fixed(INTERVAL_BETWEEN_SSH.seconds),
        reraise=True,
    )
    def run_command(
        self,
        command: Sequence[str] | str,
        timeout: Optional[int] = None,
    ) -> tuple[bytes, bytes]:
        """Run a shell command on the relay via SSH."""
        command_string = (
            " ".join(command)
            if isinstance(command, Sequence) and not isinstance(command, str)
            else command
        )

        ssh_client = paramiko_client.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            self.address,
            port=self.port,
            username=self.username,
            password=self.password,
            look_for_keys=False,
        )
        transport = ssh_client.get_transport()
        if transport is not None:
            transport.set_keepalive(DEFAULT_KEEPALIVE)
        logger.debug("Running command %s", command_string)
        _, stdout, stderr = ssh_client.exec_command(
            command=command_string, timeout=timeout, get_pty=True
        )
        out = stdout.read()
        err = stderr.read()
        ssh_client.close()
        return out, err

    @tenacity.retry(
        stop=tenacity.stop.stop_after_attempt(MAX_SSH_TRIES),
        retry=tenacity.retry_if_exception_type(
            (ssh_exception.SSHException, TimeoutError)
        ),
        wait=tenacity.wait.wait_fixed(INTERVAL_BETWEEN_SSH.seconds),
        reraise=True,
    )
    def upload_file(
        self,
        remote_path: str,
        content: bytes,
        timeout: float | None = DEFAULT_UPLOAD_TIMEOUT,
    ) -> None:
        """Upload bytes to a path on the relay via SFTP."""
        transport = paramiko.Transport((self.address, self.port))
        transport.set_keepalive(DEFAULT_KEEPALIVE)
        if self.username is not None:
            transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        if timeout is not None and sftp is not None:
            channel = sftp.get_channel()
            if channel is not None:
                channel.settimeout(timeout=timeout)
        with tempfile.NamedTemporaryFile("wb") as tmp:
            tmp.write(content)
            tmp.flush()
            if sftp is not None:
                sftp.put(tmp.name, remote_path)
                sftp.close()
        transport.close()
