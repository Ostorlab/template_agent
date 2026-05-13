"""Base class for anti-tampering checks."""

import abc
import logging
import time

from ostorlab.agent.kb import kb

from agent import observation
from agent import adb_device
from agent.models import CheckContext, CheckResult, TamperResult

logger = logging.getLogger(__name__)

STARTUP_WAIT_SECONDS = 6


class TamperCheck(abc.ABC):
    name: str
    ## TODO: (ohachimOs): add KB entries
    kb_missing: kb.Entry
    kb_detected: kb.Entry

    @abc.abstractmethod
    def apply(self, content: bytes) -> bytes:
        """Tamper the APK and return the modified bytes."""

    def post_launch(self, device: adb_device.AdbDevice) -> None:
        """Optional hook called after app launch. Default: noop."""

    def run(self, content: bytes, context: CheckContext) -> CheckResult:
        tampered = self.apply(content)

        remote_path = context.device.upload_apk(tampered)
        try:
            context.device.uninstall(context.package_name)
            try:
                context.device.install(remote_path)
            except adb_device.AdbInstallError as e:
                return CheckResult(
                    self.name,
                    TamperResult.AMBIGUOUS,
                    f"Install failed: {e}",
                )
        finally:
            context.device.remove_remote_file(remote_path)

        context.device.start_app(context.package_name)
        time.sleep(STARTUP_WAIT_SECONDS)

        if context.device.is_process_alive(context.package_name) is False:
            return CheckResult(
                self.name,
                TamperResult.DETECTED,
                "App died at startup after tampering",
            )

        self.post_launch(context.device)

        return observation.observe(self.name, context)
