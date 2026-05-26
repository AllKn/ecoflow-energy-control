#!/usr/bin/env python3
"""Tiny local EcoFlow Cloud API tester.

Run this on the machine/network you want to test from. It serves a local HTML
page and proxies EcoFlow requests so your secret key never needs to be placed in
browser JavaScript.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import parse, request, error


ROOT = Path(__file__).resolve().parent
DEFAULT_HOST = "https://api-e.ecoflow.com"


class EcoFlowHandler(BaseHTTPRequestHandler):
    """Serve the tester UI and proxy API calls."""

    server_version = "EcoFlowApiTester/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send_file(ROOT / "index.html", "text/html; charset=utf-8")
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/device-list":
                result = ecoflow_request(body, "GET", "/iot-open/sign/device/list", {})
            elif self.path == "/api/quota-all":
                serial = str(body.get("serial", "")).strip()
                result = ecoflow_request(
                    body, "GET", "/iot-open/sign/device/quota/all", {"sn": serial}
                )
            elif self.path == "/api/quota-selected":
                serial = str(body.get("serial", "")).strip()
                quotas = [q.strip() for q in str(body.get("quotas", "")).splitlines() if q.strip()]
                result = ecoflow_request(
                    body,
                    "POST",
                    "/iot-open/sign/device/quota",
                    {"sn": serial, "params": {"quotas": quotas}},
                )
            else:
                self.send_error(404)
                return
            self._send_json(result)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"ok": False, "error": repr(exc)}, status=500)

    def _send_file(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, data: Any, status: int = 200) -> None:
        encoded = json.dumps(data, indent=2, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def ecoflow_request(config: dict[str, Any], method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Call EcoFlow, trying current signing first and legacy fallback on 8521."""
    for legacy in (False, True):
        result = _ecoflow_request_once(config, method, path, payload, legacy)
        data = result.get("response")
        if not _is_signature_error(data):
            return result
        result["signature_retry_reason"] = "8521 signature is wrong"
    return result


def _ecoflow_request_once(
    config: dict[str, Any], method: str, path: str, payload: dict[str, Any], legacy: bool
) -> dict[str, Any]:
    host = str(config.get("host") or DEFAULT_HOST).rstrip("/")
    access_key = str(config["accessKey"])
    secret_key = str(config["secretKey"])
    url = f"{host}{path}"
    body = dict(payload)

    if legacy:
        nonce = str(int(time.time() * 1000))
        timestamp = nonce
    else:
        nonce = str(random.randint(100000, 999999))
        timestamp = str(int(time.time() * 1000))

    sign_params = flatten(body)
    sign = sign_payload(sign_params, access_key, secret_key, nonce, timestamp, legacy)

    headers = {
        "accessKey": access_key,
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign,
    }

    req_data = None
    request_url = url
    if method == "GET":
        if body:
            request_url = f"{url}?{parse.urlencode(body)}"
        if legacy:
            headers["Content-Type"] = "application/json;charset=UTF-8"
    else:
        headers["Content-Type"] = "application/json;charset=UTF-8"
        req_data = json.dumps(body).encode()

    req = request.Request(request_url, data=req_data, headers=headers, method=method)
    started = time.time()
    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            status = resp.status
    except error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        status = exc.code

    try:
        response_json: Any = json.loads(raw)
    except json.JSONDecodeError:
        response_json = raw

    return {
        "ok": status < 400 and not _is_error_code(response_json),
        "status": status,
        "method": method,
        "url": request_url,
        "path": path,
        "legacy_signing": legacy,
        "duration_ms": round((time.time() - started) * 1000),
        "signed_keys": sorted(sign_params) + ["accessKey", "nonce", "timestamp"],
        "signing_order": "payload parameters sorted, then accessKey, nonce, timestamp"
        if not legacy
        else "legacy urlencode of all parameters",
        "response": response_json,
    }


def sign_payload(
    params: dict[str, Any],
    access_key: str,
    secret_key: str,
    nonce: str,
    timestamp: str,
    legacy: bool,
) -> str:
    if legacy:
        params = {
            **params,
            "accessKey": access_key,
            "nonce": nonce,
            "timestamp": timestamp,
        }
        encoded = parse.urlencode(sorted((key, str(value)) for key, value in params.items()))
    else:
        payload = "&".join(f"{key}={params[key]}" for key in sorted(params))
        auth = f"accessKey={access_key}&nonce={nonce}&timestamp={timestamp}"
        encoded = f"{payload}&{auth}" if payload else auth
    return hmac.new(secret_key.encode(), encoded.encode(), hashlib.sha256).hexdigest()


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten(item, child_key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            flattened.update(flatten(item, f"{prefix}[{index}]"))
    elif value is not None:
        flattened[prefix] = str(value).lower() if isinstance(value, bool) else value
    return flattened


def _is_error_code(data: Any) -> bool:
    return isinstance(data, dict) and str(data.get("code", "0")) not in ("0", "None")


def _is_signature_error(data: Any) -> bool:
    return isinstance(data, dict) and (
        str(data.get("code")) == "8521"
        or "signature is wrong" in str(data.get("message", "")).lower()
    )


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), EcoFlowHandler)
    print("EcoFlow API tester: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
