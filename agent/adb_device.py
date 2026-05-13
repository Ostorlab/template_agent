"""Minimal ADB device abstraction using a device relay."""

import datetime
import logging
import random
import uuid

import tenacity

from agent import device_relay as relay

ADB = "/usr/local/bin/adb"
MAX_INSTALL_RETRIES = 3
INSTALL_RETRY_WAIT = datetime.timedelta(seconds=5)

logger = logging.getLogger(__name__)


class AdbInstallError(Exception):
    pass


class AdbDevice:
    """Wraps ADB commands via SSH relay for a specific device serial."""

    def __init__(self, device_serial: str, device_relay: relay.DeviceRelay) -> None:
        self.device_serial = device_serial
        self.device_relay = device_relay

    def _run(self, args: list[str], timeout: int = 30) -> tuple[bytes, bytes]:
        cmd = [ADB, "-s", self.device_serial] + args
        return self.device_relay.run_command(cmd, timeout=timeout)

    def upload_apk(self, content: bytes) -> str:
        """Upload APK bytes to relay machine. Returns remote path."""
        remote_path = f"/tmp/{random.randint(1000, 9999)}_{uuid.uuid4()}.apk"
        self.device_relay.upload_file(remote_path, content)
        return remote_path

    def uninstall(self, package_name: str) -> None:
        stdout, _ = self._run(["uninstall", package_name])
        logger.info("uninstall %s: %s", package_name, stdout.decode(errors="ignore"))

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(MAX_INSTALL_RETRIES),
        wait=tenacity.wait_fixed(INSTALL_RETRY_WAIT.total_seconds()),
        retry=tenacity.retry_if_exception_type(AdbInstallError),
        reraise=True,
    )
    def install(self, remote_apk_path: str) -> None:
        """Install APK from path on the relay machine."""
        stdout, stderr = self._run(["install", "-r", remote_apk_path], timeout=120)
        combined = (stdout + stderr).decode(errors="ignore")
        logger.info("install output: %s", combined)
        if "success" not in combined.lower():
            raise AdbInstallError(combined[:300])

    def start_app(self, package_name: str) -> None:
        """Launch app via adb monkey (1 LAUNCHER event)."""
        self._run(
            [
                "shell",
                "monkey",
                "-p",
                package_name,
                "--pct-syskeys",
                "0",
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ]
        )

    def is_process_alive(self, package_name: str) -> bool:
        stdout, _ = self._run(["shell", "ps", "-A"])
        return package_name.encode() in stdout

    def remove_remote_file(self, remote_path: str) -> None:
        self.device_relay.run_command(f"rm -f {remote_path}")
