"""Async client for the EcoFlow signed cloud API."""

from __future__ import annotations

import hashlib
import hmac
import json
import random
import time
from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientSession


class EcoFlowApiError(RuntimeError):
    """Raised when EcoFlow returns an unexpected response."""


class EcoFlowCloudClient:
    """Small EcoFlow REST client.

    EcoFlow's public API signs query/body parameters with HMAC-SHA256. Device
    command payloads differ per product, so commands are deliberately passed in
    as dictionaries from configuration.
    """

    def __init__(
        self,
        session: ClientSession,
        host: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        self._session = session
        self._host = host.rstrip("/")
        self._access_key = access_key
        self._secret_key = secret_key

    async def get_device_quotas(self, serial: str, quotas: list[str] | None) -> dict[str, Any]:
        """Read selected or all quotas for a device."""
        if quotas:
            payload: dict[str, Any] = {"sn": serial, "params": {"quotas": quotas}}
            return await self._request("POST", "/iot-open/sign/device/quota", payload)
        return await self._request(
            "GET", "/iot-open/sign/device/quota/all", {"sn": serial}
        )

    async def get_devices(self) -> dict[str, Any]:
        """List devices linked to the EcoFlow developer account."""
        return await self._request("GET", "/iot-open/sign/device/list", {})

    async def set_device_command(self, serial: str, command: Mapping[str, Any]) -> dict[str, Any]:
        """Send a configured command to a device."""
        payload = dict(command)
        payload["sn"] = serial
        return await self._request("PUT", "/iot-open/sign/device/quota", payload)

    async def _request(
        self, method: str, path: str, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        body = dict(payload)
        url = f"{self._host}{path}"
        data = await self._send(method, url, body, legacy=False)

        if self._is_signature_error(data):
            data = await self._send(method, url, body, legacy=True)

        if not isinstance(data, dict):
            raise EcoFlowApiError(f"Unexpected EcoFlow response: {data!r}")
        code = data.get("code")
        if code not in (0, "0", None):
            raise EcoFlowApiError(str(data))
        return data

    async def _send(
        self, method: str, url: str, body: dict[str, Any], legacy: bool
    ) -> dict[str, Any]:
        nonce = str(int(time.time() * 1000)) if legacy else str(random.randint(100000, 999999))
        sign_params = self._flatten(body)
        sign_params["accessKey"] = self._access_key
        sign_params["nonce"] = nonce
        sign_params["timestamp"] = nonce
        sign = self._legacy_sign(sign_params) if legacy else self._sign(sign_params)
        headers = {
            "accessKey": self._access_key,
            "nonce": nonce,
            "timestamp": nonce,
            "sign": sign,
        }
        if legacy or method != "GET":
            headers["Content-Type"] = "application/json;charset=UTF-8"

        if method == "GET":
            async with self._session.get(url, headers=headers, params=body) as resp:
                return await resp.json(content_type=None)
        async with self._session.request(method, url, headers=headers, json=body) as resp:
            return await resp.json(content_type=None)

    def _sign(self, params: Mapping[str, Any]) -> str:
        encoded = "&".join(f"{key}={params[key]}" for key in sorted(params))
        digest = hmac.new(
            self._secret_key.encode(), encoded.encode(), hashlib.sha256
        ).hexdigest()
        return digest

    def _legacy_sign(self, params: Mapping[str, Any]) -> str:
        encoded = urlencode(sorted((key, str(value)) for key, value in params.items()))
        return hmac.new(
            self._secret_key.encode(), encoded.encode(), hashlib.sha256
        ).hexdigest()

    def _is_signature_error(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        return str(data.get("code")) == "8521" or "signature is wrong" in str(
            data.get("message", "")
        ).lower()

    def _flatten(self, value: Any, prefix: str = "") -> dict[str, Any]:
        flattened: dict[str, Any] = {}
        if isinstance(value, Mapping):
            for key, item in value.items():
                child_key = f"{prefix}.{key}" if prefix else str(key)
                flattened.update(self._flatten(item, child_key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                flattened.update(self._flatten(item, f"{prefix}[{index}]"))
        elif value is not None:
            flattened[prefix] = str(value).lower() if isinstance(value, bool) else value
        return flattened


def render_template_dict(template: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    """Render simple {{ key }} placeholders in a JSON-like command dictionary."""
    encoded = json.dumps(deepcopy(template))
    for key, value in values.items():
        encoded = encoded.replace(f'"{{{{ {key} }}}}"', json.dumps(value))
        encoded = encoded.replace(f"{{{{ {key} }}}}", str(value))
    return json.loads(encoded)
