"""SMA cloud API reader."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientSession


async def read_sma_device(
    session: ClientSession,
    host: str,
    token: str,
    plant_id: str,
    device: dict[str, Any],
    endpoint_template: str,
) -> dict[str, Any]:
    """Read one SMA device through a configurable SMA cloud endpoint.

    SMA's public developer APIs require an application and OAuth token. The URL
    template keeps this integration usable across Monitoring API and Live API
    endpoint variants without hardcoding a private contract.
    """
    device_id = str(device.get("device_id", ""))
    path = endpoint_template.format(plant_id=plant_id, device_id=device_id)
    url = f"{host.rstrip('/')}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    async with session.get(url, headers=headers) as resp:
        data = await resp.json(content_type=None)
    return {
        "available": True,
        "name": device.get("name", device_id),
        "device_id": device_id,
        "ac_power_w": _find_number(data, ("ac_power_w", "power", "Pac", "PV_POWER")),
        "daily_yield_wh": _find_number(data, ("daily_yield_wh", "E_DAY", "dayYield")),
        "total_yield_wh": _find_number(data, ("total_yield_wh", "E_TOTAL", "totalYield")),
        "raw": data,
    }


def _find_number(value: Any, keys: tuple[str, ...]) -> float | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys:
                try:
                    return float(item)
                except (TypeError, ValueError):
                    pass
            found = _find_number(item, keys)
            if found is not None:
                return found
    if isinstance(value, list):
        for item in value:
            found = _find_number(item, keys)
            if found is not None:
                return found
    return None
