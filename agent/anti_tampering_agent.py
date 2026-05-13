"""Anti-Tampering Detection Agent."""

import logging
import time

from androguard.core import apk as androguard_apk
from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as msg
from ostorlab.agent.mixins import agent_report_vulnerability_mixin as vuln_mixin
from ostorlab.runtimes import definitions as runtime_definitions
from rich import logging as rich_logging

from agent import adb_device
from agent import device_relay
from agent.checks.base import TamperCheck, STARTUP_WAIT_SECONDS
from agent.models import CheckContext, CheckResult, TamperResult

logging.basicConfig(
    format="%(message)s",
    datefmt="[%X]",
    level="INFO",
    force=True,
    handlers=[rich_logging.RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

SELECTOR_APK = "v3.asset.file.android.apk"

## TODO: (ohachimOs) Add checks in upcoming PRs.
CHECKS: list[TamperCheck] = []


class AntiTamperingAgent(agent.Agent, vuln_mixin.AgentReportVulnMixin):
    """Detects missing or working anti-tampering protections in Android apps."""

    def __init__(
        self,
        agent_definition: agent_definitions.AgentDefinition,
        agent_settings: runtime_definitions.AgentSettings,
    ) -> None:
        super().__init__(agent_definition, agent_settings)
        self._relay_address: str = self.args.get("relay_address", "127.0.0.1")
        self._relay_port: int = self.args.get("relay_port", 22)
        self._relay_username: str = self.args.get("relay_username", "")
        self._relay_password: str = self.args.get("relay_password", "")
        self._device_serial: str = self.args.get("device_name", "emulator-5554")
        self._device_version: str = self.args.get("device_version", "10.0")
        self._vision_api_key: str = self.args.get("vision_api_key", "")
        self._vision_model: str = self.args.get("vision_model", "google/gemini-2.5-pro")

    def process(self, message: msg.Message) -> None:
        if message.selector == SELECTOR_APK:
            self._process_apk(message)
        else:
            logger.error("Unexpected selector: %s", message.selector)

    def _process_apk(self, message: msg.Message) -> None:
        content: bytes | None = message.data.get("content")
        if content is None:
            logger.error("No APK content in message.")
            return

        apk_obj = androguard_apk.APK(content, raw=True)  # type: ignore[arg-type]
        package_name = str(apk_obj.get_package())
        main_activities = apk_obj.get_main_activities()
        main_activity = list(main_activities)[0] if main_activities else ""
        logger.info("Package: %s  Main activity: %s", package_name, main_activity)

        # TODO: (ohachimOs) add prepare dyanmic mcp server calls to allocate device, or allocate device directly with scanning engine calls
        relay = device_relay.DeviceRelay(
            address=self._relay_address,
            port=self._relay_port,
            username=self._relay_username,
            password=self._relay_password,
        )
        context = CheckContext(
            device=adb_device.AdbDevice(
                device_serial=self._device_serial, device_relay=relay
            ),
            package_name=package_name,
            main_activity=main_activity,
            device_version=self._device_version,
            vision_api_key=self._vision_api_key,
            vision_model=self._vision_model,
        )

        if self._baseline_app_crashes(content, context) is True:
            logger.error(
                "Baseline FAILED: original APK does not run on this device. "
                "All anti-tampering checks skipped."
            )
            return

        try:
            for check in CHECKS:
                logger.info("Running check: %s", check.name)
                result = check.run(content, context)
                logger.info(
                    "Check %s: %s — %s",
                    result.check_name,
                    result.result.value,
                    result.evidence,
                )
                self._report(check, result, package_name)
        finally:
            context.device.uninstall(context.package_name)

    def _baseline_app_crashes(self, content: bytes, context: CheckContext) -> bool:
        """Install and launch the original APK. Returns True if the process dies on its own."""
        remote_path = context.device.upload_apk(content)
        try:
            context.device.uninstall(context.package_name)
            try:
                context.device.install(remote_path)
            except adb_device.AdbInstallError as e:
                logger.error("Baseline install failed: %s", e)
                return True
        finally:
            context.device.remove_remote_file(remote_path)

        context.device.start_app(context.package_name)
        time.sleep(STARTUP_WAIT_SECONDS)
        alive = context.device.is_process_alive(context.package_name)
        context.device.uninstall(context.package_name)

        if alive is False:
            return True
        logger.info("Baseline OK: original APK runs fine.")
        return False

    def _report(
        self, check: TamperCheck, result: CheckResult, package_name: str
    ) -> None:
        if result.result == TamperResult.NOT_DETECTED:
            self.report_vulnerability(
                entry=check.kb_missing,
                technical_detail=(
                    f"`{package_name}` ran normally after tampering (check: {result.check_name}). "
                    f"{result.evidence}"
                ),
                risk_rating=vuln_mixin.RiskRating.MEDIUM,
            )
        elif result.result == TamperResult.DETECTED:
            self.report_vulnerability(
                entry=check.kb_detected,
                technical_detail=(
                    f"`{package_name}` detected tampering (check: {result.check_name}). "
                    f"{result.evidence}"
                ),
                risk_rating=vuln_mixin.RiskRating.INFO,
            )
        else:
            logger.warning(
                "Ambiguous result for %s: %s", result.check_name, result.evidence
            )


if __name__ == "__main__":
    logger.info("starting agent ...")
    AntiTamperingAgent.main()
