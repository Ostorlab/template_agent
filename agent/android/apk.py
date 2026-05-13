"""APK manipulation helpers: sign, decompile, build."""

import logging
import os
import pathlib
import subprocess
import tempfile
import uuid
from collections.abc import Sequence

logger = logging.getLogger(__name__)

_ANDROID_DIR = pathlib.Path(__file__).parent
APK_TOOL_PATH = _ANDROID_DIR / "apktool_2.9.2.jar"
APK_SIGNER_PATH = _ANDROID_DIR / "uber-apk-signer-1.3.0.jar"


class CommandExecutionError(Exception):
    """Raised when a subprocess command fails."""


def _exec(command: Sequence[str | os.PathLike[str]]) -> None:
    try:
        result = subprocess.run(command, capture_output=True, check=True)
        if (err := result.stderr.decode()) != "":
            logger.error("Command stderr: %s", err)
    except subprocess.CalledProcessError as e:
        logger.error("Command failed: %s", e.output)
        raise CommandExecutionError(
            f"Command {e.cmd} failed: {e.stderr.decode()}"
        ) from e


def sign_apk(apk_path: str) -> str:
    """Re-sign APK with uber-apk-signer using a fresh debug key.

    Returns the output directory containing the signed APK (named *-aligned-debugSigned.apk).
    """
    output_dir = f"/tmp/{uuid.uuid4()}"
    _exec(
        [
            "java",
            "-jar",
            str(APK_SIGNER_PATH),
            "--allowResign",
            "-a",
            apk_path,
            "-o",
            output_dir,
        ]
    )
    return output_dir


def decompile_apk(content: bytes) -> str:
    """Decompile APK to smali using apktool. Returns path to decompiled directory."""
    output_dir = f"/tmp/app_{uuid.uuid4()}"
    with tempfile.NamedTemporaryFile(suffix=".apk", delete=False) as f:
        f.write(content)
        tmp_path = f.name
    try:
        _exec(
            ["java", "-jar", str(APK_TOOL_PATH), "-f", "d", tmp_path, "-o", output_dir]
        )
    finally:
        os.unlink(tmp_path)
    return output_dir


def build_apk(app_path: str) -> str:
    """Rebuild APK from decompiled directory using apktool. Returns path to built APK."""
    output_path = f"/tmp/{uuid.uuid4()}.apk"
    _exec(
        [
            "java",
            "-jar",
            str(APK_TOOL_PATH),
            "-f",
            "b",
            app_path,
            "--use-aapt2",
            "-o",
            output_path,
        ]
    )
    return output_path
