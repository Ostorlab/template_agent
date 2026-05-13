"""Observation logic: runs monkey_tester interaction and uses a vision model to detect tampering."""

import asyncio
import base64
import datetime
import io
import logging
import os
import zipfile
from typing import Any

import httpx
import mcp
import mcp.types
import pydantic
import pydantic_ai
import tenacity
from mcp.client import streamable_http

from agent import ai_model
from agent.models import CheckContext, CheckResult, TamperResult

logger = logging.getLogger(__name__)

MONKEY_TESTER_URL = os.environ.get(
    "MONKEY_TESTER_URL", "http://monkey_tester:50051/mcp"
)
MCP_TIMEOUT = datetime.timedelta(minutes=30)
MAX_INTERACTION_RETRIES = 3
MAX_VISION_RETRIES = 3

INTERACTION_PROMPT = (
    "Open the app if not already open. Interact with all features — click every button "
    "and explore every screen."
)

VISION_SYSTEM_PROMPT = (
    "You are a mobile security analyst. Analyze this Android app screenshot and determine "
    "if the app has detected tampering or repackaging. Look for: security warning dialogs, "
    "messages containing words like tampered, modified, invalid signature, integrity, "
    "repackaged, or any crash/error dialog that appeared after the app was modified. "
    "Be concise."
)


class _ScreenshotAnalysis(pydantic.BaseModel):
    anti_tamper_detected: bool
    evidence: str


@tenacity.retry(
    stop=tenacity.stop_after_attempt(MAX_INTERACTION_RETRIES),
    wait=tenacity.wait_exponential(multiplier=2, min=2, max=30),
    retry=tenacity.retry_if_exception_type(
        (httpx.TransportError, httpx.TimeoutException)
    ),
    reraise=True,
)
async def _call_interact(context: CheckContext) -> bytes | None:
    relay = context.device.device_relay
    device_info: dict[str, Any] = {
        "platform": "android",
        "device_id": context.device.device_serial,
        "version": context.device_version,
        "relay_address": relay.address,
        "relay_port": relay.port,
        "relay_username": relay.username,
        "relay_password": relay.password,
    }
    app_info: dict[str, Any] = {
        "package_name": context.package_name,
        "main_activity": context.main_activity,
        "is_flutter_app": False,
        "is_debug_enabled": False,
    }
    http_client = httpx.AsyncClient(timeout=MCP_TIMEOUT.total_seconds())
    async with streamable_http.streamable_http_client(
        url=MONKEY_TESTER_URL, http_client=http_client
    ) as (reader, writer, _):
        async with mcp.ClientSession(reader, writer) as session:
            await session.initialize()
            result = await session.call_tool(
                name="interact",
                arguments={
                    "prompt": INTERACTION_PROMPT,
                    "device_info": device_info,
                    "app_info": app_info,
                },
            )
            if result.isError is True:
                error_text = (
                    result.content[0].text
                    if result.content
                    and isinstance(result.content[0], mcp.types.TextContent)
                    else "unknown"
                )
                logger.error("monkey_tester interact failed: %s", error_text)
                return None
            for content in result.content:
                if isinstance(content, mcp.types.TextContent):
                    return base64.b64decode(content.text)
    return None


def _extract_screenshots(screenshots_zip: bytes) -> list[bytes]:
    screenshots: list[bytes] = []
    with zipfile.ZipFile(io.BytesIO(screenshots_zip), "r") as zf:
        for name in zf.namelist():
            screenshots.append(zf.read(name))
    return screenshots


@tenacity.retry(
    stop=tenacity.stop_after_attempt(MAX_VISION_RETRIES),
    wait=tenacity.wait_exponential(multiplier=2, min=2, max=30),
    retry=tenacity.retry_if_exception_type(
        (httpx.TransportError, httpx.TimeoutException)
    ),
    reraise=True,
)
async def _analyze_screenshot(
    screenshot: bytes, api_key: str, model_identifier: str
) -> _ScreenshotAnalysis:
    model = ai_model.get_vision_model(model_identifier, api_key)
    agent: pydantic_ai.Agent[None, _ScreenshotAnalysis] = pydantic_ai.Agent(
        model=model,
        system_prompt=VISION_SYSTEM_PROMPT,
        output_type=_ScreenshotAnalysis,
    )
    result = await agent.run(
        [pydantic_ai.BinaryContent(data=screenshot, media_type="image/png")]
    )
    return result.output


def observe(check_name: str, context: CheckContext) -> CheckResult:
    screenshots_zip = asyncio.run(_call_interact(context))

    if screenshots_zip is None:
        if context.device.is_process_alive(context.package_name) is False:
            return CheckResult(
                check_name,
                TamperResult.DETECTED,
                "App died during interaction after tampering",
            )
        return CheckResult(
            check_name,
            TamperResult.AMBIGUOUS,
            "monkey_tester could not interact with app (NonResponsiveApplication)",
        )

    screenshots = _extract_screenshots(screenshots_zip)
    if len(screenshots) == 0:
        return CheckResult(
            check_name,
            TamperResult.AMBIGUOUS,
            "monkey_tester returned no screenshots",
        )

    for screenshot in screenshots:
        analysis = asyncio.run(
            _analyze_screenshot(
                screenshot, context.vision_api_key, context.vision_model
            )
        )
        if analysis.anti_tamper_detected is True:
            return CheckResult(check_name, TamperResult.DETECTED, analysis.evidence)

    return CheckResult(
        check_name,
        TamperResult.NOT_DETECTED,
        "App ran normally — no anti-tampering response detected",
    )
