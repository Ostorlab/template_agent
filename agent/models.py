"""Shared data structures for anti-tampering checks."""

import dataclasses
import enum

from agent import adb_device


class TamperResult(enum.Enum):
    DETECTED = "detected"
    NOT_DETECTED = "not_detected"
    AMBIGUOUS = "ambiguous"


@dataclasses.dataclass
class CheckResult:
    check_name: str
    result: TamperResult
    evidence: str


@dataclasses.dataclass
class CheckContext:
    device: adb_device.AdbDevice
    package_name: str
    main_activity: str
    device_version: str
    vision_api_key: str
    vision_model: str
