"""Pytest fixtures for the AntiTampering agent."""

import io
import json
import pathlib
import zipfile
from collections.abc import Callable

import pytest
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.utils import definitions as utils_definitions

from agent import adb_device as adb_device_module
from agent import anti_tampering_agent
from agent import device_relay as device_relay_module
from agent import models


@pytest.fixture()
def tampering_agent(
    agent_mock: list[message.Message],
) -> anti_tampering_agent.AntiTamperingAgent:
    del agent_mock
    with (pathlib.Path(__file__).parent.parent / "oxo.yaml").open() as yaml_f:
        definition = agent_definitions.AgentDefinition.from_yaml(yaml_f)
        settings = runtime_definitions.AgentSettings(
            key="agent/ostorlab/anti_tampering",
            bus_url="NA",
            bus_exchange_topic="NA",
            args=[
                utils_definitions.Arg(
                    name="relay_address",
                    type="string",
                    value=json.dumps("127.0.0.1").encode(),
                ),
                utils_definitions.Arg(
                    name="relay_port", type="number", value=json.dumps(22).encode()
                ),
                utils_definitions.Arg(
                    name="relay_username",
                    type="string",
                    value=json.dumps("test_user").encode(),
                ),
                utils_definitions.Arg(
                    name="relay_password",
                    type="string",
                    value=json.dumps("test_pass").encode(),
                ),
                utils_definitions.Arg(
                    name="device_name",
                    type="string",
                    value=json.dumps("emulator-5554").encode(),
                ),
                utils_definitions.Arg(
                    name="device_version",
                    type="string",
                    value=json.dumps("10.0").encode(),
                ),
                utils_definitions.Arg(
                    name="vision_api_key",
                    type="string",
                    value=json.dumps("test_key").encode(),
                ),
                utils_definitions.Arg(
                    name="vision_model",
                    type="string",
                    value=json.dumps("google/gemini-2.5-pro").encode(),
                ),
            ],
            healthcheck_port=5301,
            redis_url="redis://guest:guest@localhost:6379",
        )
        return anti_tampering_agent.AntiTamperingAgent(definition, settings)


@pytest.fixture()
def fake_apk_message() -> message.Message:
    return message.Message.from_data(
        "v3.asset.file.android.apk",
        data={"content": b"FAKE_APK_CONTENT", "path": "test.apk"},
    )


@pytest.fixture()
def relay() -> device_relay_module.DeviceRelay:
    return device_relay_module.DeviceRelay(
        address="127.0.0.1", port=22, username="user", password="pass"
    )


@pytest.fixture()
def adb_device_obj(
    relay: device_relay_module.DeviceRelay,
) -> adb_device_module.AdbDevice:
    return adb_device_module.AdbDevice(
        device_serial="emulator-5554", device_relay=relay
    )


@pytest.fixture()
def check_context(
    adb_device_obj: adb_device_module.AdbDevice,
) -> models.CheckContext:
    return models.CheckContext(
        device=adb_device_obj,
        package_name="com.test.app",
        main_activity="com.test.app.MainActivity",
        device_version="10.0",
        vision_api_key="test_key",
        vision_model="google/gemini-test",
    )


@pytest.fixture()
def screenshot_zip() -> Callable[..., bytes]:
    def _make(*images: bytes) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i, img in enumerate(images):
                zf.writestr(f"screenshot_{i}.png", img)
        return buf.getvalue()

    return _make
