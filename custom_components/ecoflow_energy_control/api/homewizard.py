"""HomeWizard local API reader."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientSession


async def read_homewizard_meter(
    session: ClientSession, meter: dict[str, Any]
) -> dict[str, Any]:
    """Read a HomeWizard Energy device through the local v1 API."""
    host = str(meter["host"]).strip()
    base_url = host if host.startswith(("http://", "https://")) else f"http://{host}"
    async with session.get(f"{base_url.rstrip('/')}/api/v1/data") as resp:
        data = await resp.json(content_type=None)

    phases = {
        "l1": _number(data.get("active_power_l1_w")),
        "l2": _number(data.get("active_power_l2_w")),
        "l3": _number(data.get("active_power_l3_w")),
    }
    active_power = _number(data.get("active_power_w"))
    return {
        "available": True,
        "name": meter.get("name", host),
        "host": host,
        "role": meter.get("role", "solar_total"),
        "active_power_w": active_power,
        "phase_power_w": phases,
        "raw": data,
    }


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
