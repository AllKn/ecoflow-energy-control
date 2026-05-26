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
    voltages = {
        "l1": _number(data.get("active_voltage_l1_v")),
        "l2": _number(data.get("active_voltage_l2_v")),
        "l3": _number(data.get("active_voltage_l3_v")),
    }
    currents = {
        "l1": _number(data.get("active_current_l1_a")),
        "l2": _number(data.get("active_current_l2_a")),
        "l3": _number(data.get("active_current_l3_a")),
    }
    active_power = _number(data.get("active_power_w"))
    return {
        "available": True,
        "name": meter.get("name", host),
        "host": host,
        "role": meter.get("role", "solar_total"),
        "active_power_w": active_power,
        "phase_power_w": phases,
        "phase_voltage_v": voltages,
        "phase_current_a": currents,
        "total_power_import_kwh": _sum_numbers(
            data.get("total_power_import_t1_kwh"),
            data.get("total_power_import_t2_kwh"),
        ),
        "total_power_export_kwh": _sum_numbers(
            data.get("total_power_export_t1_kwh"),
            data.get("total_power_export_t2_kwh"),
        ),
        "wifi_ssid": data.get("wifi_ssid"),
        "wifi_strength": _number(data.get("wifi_strength")),
        "meter_model": data.get("product_name") or data.get("product_type"),
        "raw": data,
    }


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_numbers(*values: Any) -> float | None:
    numbers = [_number(value) for value in values]
    valid = [value for value in numbers if value is not None]
    if not valid:
        return None
    return round(sum(valid), 5)
