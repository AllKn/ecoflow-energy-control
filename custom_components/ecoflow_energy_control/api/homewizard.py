"""HomeWizard local API reader."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant

from ..power import normalize_homewizard_power_w


async def read_homewizard_meter(
    session: ClientSession, meter: dict[str, Any]
) -> dict[str, Any]:
    """Read a HomeWizard Energy device through the local v1 API."""
    host = str(meter["host"]).strip()
    base_url = host if host.startswith(("http://", "https://")) else f"http://{host}"
    async with session.get(f"{base_url.rstrip('/')}/api/v1/data") as resp:
        data = await resp.json(content_type=None)

    phases = {
        "l1": _optional_normalized_power(data.get("active_power_l1_w")),
        "l2": _optional_normalized_power(data.get("active_power_l2_w")),
        "l3": _optional_normalized_power(data.get("active_power_l3_w")),
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
    active_power = _optional_normalized_power(data.get("active_power_w"))
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


def read_homewizard_ha_meter(hass: HomeAssistant, meter: dict[str, Any]) -> dict[str, Any]:
    """Read a HomeWizard device through existing Home Assistant entities."""
    entities = meter.get("entities", {})
    phases = {
        "l1": _optional_normalized_power(_state_number(hass, entities.get("power_l1"))),
        "l2": _optional_normalized_power(_state_number(hass, entities.get("power_l2"))),
        "l3": _optional_normalized_power(_state_number(hass, entities.get("power_l3"))),
    }
    active_power = _optional_normalized_power(_state_number(hass, entities.get("power")))
    if active_power is None:
        active_power = _sum_existing(*phases.values())
    return {
        "available": True,
        "name": meter.get("name", "HomeWizard"),
        "host": meter.get("device_id", meter.get("name", "homewizard")),
        "role": meter.get("role", "solar_total"),
        "source": "homeassistant",
        "active_power_w": active_power,
        "phase_power_w": phases,
        "phase_voltage_v": {
            "l1": _state_number(hass, entities.get("voltage_l1")),
            "l2": _state_number(hass, entities.get("voltage_l2")),
            "l3": _state_number(hass, entities.get("voltage_l3")),
        },
        "phase_current_a": {
            "l1": _state_number(hass, entities.get("current_l1")),
            "l2": _state_number(hass, entities.get("current_l2")),
            "l3": _state_number(hass, entities.get("current_l3")),
        },
        "total_power_import_kwh": _sum_states(
            hass,
            entities.get("energy_import"),
            entities.get("energy_import_t1"),
            entities.get("energy_import_t2"),
        ),
        "total_power_export_kwh": _sum_states(
            hass,
            entities.get("energy_export"),
            entities.get("energy_export_t1"),
            entities.get("energy_export_t2"),
        ),
        "meter_model": meter.get("model"),
        "raw": {"entities": entities},
    }


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_normalized_power(value: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return normalize_homewizard_power_w(number)


def _sum_numbers(*values: Any) -> float | None:
    numbers = [_number(value) for value in values]
    valid = [value for value in numbers if value is not None]
    if not valid:
        return None
    return round(sum(valid), 5)


def _state_number(hass: HomeAssistant, entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        return None
    return _number(state.state)


def _sum_states(hass: HomeAssistant, *entity_ids: str | None) -> float | None:
    return _sum_existing(*(_state_number(hass, entity_id) for entity_id in entity_ids))


def _sum_existing(*values: float | None) -> float | None:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return round(sum(valid), 5)
