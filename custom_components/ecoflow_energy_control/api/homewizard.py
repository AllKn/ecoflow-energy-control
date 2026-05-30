"""HomeWizard local API reader."""

from __future__ import annotations

from datetime import datetime, timedelta
from inspect import signature
from typing import Any

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..power import normalize_homewizard_power_w


async def read_homewizard_meter(
    session: ClientSession, meter: dict[str, Any]
) -> dict[str, Any]:
    """Read a HomeWizard Energy device through the local v1 API."""
    host = str(meter["host"]).strip()
    base_url = host if host.startswith(("http://", "https://")) else f"http://{host}"
    async with session.get(f"{base_url.rstrip('/')}/api/v1/data") as resp:
        data = await resp.json(content_type=None)

    role = meter.get("role", "solar_total")
    allow_deciwatts = role != "grid_meter"
    phases = {
        "l1": _optional_normalized_power(
            data.get("active_power_l1_w"), allow_deciwatts=allow_deciwatts
        ),
        "l2": _optional_normalized_power(
            data.get("active_power_l2_w"), allow_deciwatts=allow_deciwatts
        ),
        "l3": _optional_normalized_power(
            data.get("active_power_l3_w"), allow_deciwatts=allow_deciwatts
        ),
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
    active_power = _optional_normalized_power(
        data.get("active_power_w"), allow_deciwatts=allow_deciwatts
    )
    return {
        "available": True,
        "name": meter.get("name", host),
        "host": host,
        "role": role,
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
    role = meter.get("role", "solar_total")
    allow_deciwatts = role != "grid_meter"
    phases = {
        "l1": _optional_normalized_power(
            _state_number(hass, entities.get("power_l1")),
            allow_deciwatts=allow_deciwatts,
        ),
        "l2": _optional_normalized_power(
            _state_number(hass, entities.get("power_l2")),
            allow_deciwatts=allow_deciwatts,
        ),
        "l3": _optional_normalized_power(
            _state_number(hass, entities.get("power_l3")),
            allow_deciwatts=allow_deciwatts,
        ),
    }
    active_power = _optional_normalized_power(
        _state_number(hass, entities.get("power")),
        allow_deciwatts=allow_deciwatts,
    )
    if active_power is None:
        active_power = _sum_existing(*phases.values())
    return {
        "available": True,
        "name": meter.get("name", "HomeWizard"),
        "host": meter.get("device_id", meter.get("name", "homewizard")),
        "role": role,
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


async def read_homewizard_ha_history(
    hass: HomeAssistant, meter: dict[str, Any]
) -> dict[str, Any]:
    """Read P1 import/export history from Home Assistant statistics."""
    if meter.get("role") != "grid_meter":
        return {"available": False, "reason": "alleen P1/netmeter"}

    entities = meter.get("entities", {})
    import_entities = _existing_entities(
        entities.get("energy_import"),
        entities.get("energy_import_t1"),
        entities.get("energy_import_t2"),
    )
    export_entities = _existing_entities(
        entities.get("energy_export"),
        entities.get("energy_export_t1"),
        entities.get("energy_export_t2"),
    )
    if not import_entities and not export_entities:
        return {"available": False, "reason": "geen energie-entiteiten"}

    now = dt_util.now()
    starts = {
        "today": now.replace(hour=0, minute=0, second=0, microsecond=0),
        "week": (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ),
        "month": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
    }
    periods: dict[str, dict[str, float | None]] = {}
    errors: dict[str, str] = {}
    for key, start in starts.items():
        try:
            imported = await _statistics_delta(hass, import_entities, start, now)
            exported = await _statistics_delta(hass, export_entities, start, now)
            periods[key] = {
                "import_kwh": imported,
                "export_kwh": exported,
                "net_import_kwh": _net_import(imported, exported),
            }
        except Exception as err:  # noqa: BLE001
            errors[key] = str(err)
            periods[key] = {
                "import_kwh": None,
                "export_kwh": None,
                "net_import_kwh": None,
            }

    return {
        "available": not errors,
        "source": "homeassistant_statistics",
        "import_entities": import_entities,
        "export_entities": export_entities,
        "periods": periods,
        "errors": errors,
    }


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_normalized_power(
    value: Any, *, allow_deciwatts: bool = True
) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return normalize_homewizard_power_w(number, allow_deciwatts=allow_deciwatts)


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


def _existing_entities(*entity_ids: str | None) -> list[str]:
    return [entity_id for entity_id in entity_ids if entity_id]


def _net_import(imported: float | None, exported: float | None) -> float | None:
    if imported is None and exported is None:
        return None
    return round(float(imported or 0) - float(exported or 0), 5)


async def _statistics_delta(
    hass: HomeAssistant,
    entity_ids: list[str],
    start: datetime,
    end: datetime,
) -> float | None:
    deltas: list[float] = []
    for entity_id in entity_ids:
        delta = await _entity_statistics_delta(hass, entity_id, start, end)
        if delta is not None:
            deltas.append(delta)
    if not deltas:
        return None
    return round(sum(deltas), 5)


async def _entity_statistics_delta(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
) -> float | None:
    from homeassistant.components.recorder import get_instance
    from homeassistant.components.recorder.statistics import statistics_during_period

    def load_statistics() -> dict[str, list[dict[str, Any]]]:
        return _call_statistics_during_period(
            statistics_during_period,
            hass,
            start,
            end,
            entity_id,
        )

    recorder = get_instance(hass)
    if recorder and hasattr(recorder, "async_add_executor_job"):
        stats = await recorder.async_add_executor_job(load_statistics)
    else:
        stats = await hass.async_add_executor_job(load_statistics)
    points = stats.get(entity_id) or []
    values = [
        _number(point.get("sum", point.get("state")))
        for point in points
        if isinstance(point, dict)
    ]
    valid = [value for value in values if value is not None]
    if len(valid) < 2:
        return None
    return round(valid[-1] - valid[0], 5)


def _call_statistics_during_period(
    statistics_during_period: Any,
    hass: HomeAssistant,
    start: datetime,
    end: datetime,
    entity_id: str,
) -> dict[str, list[dict[str, Any]]]:
    parameters = signature(statistics_during_period).parameters
    kwargs: dict[str, Any] = {}
    if "units" in parameters:
        kwargs["units"] = None
    if "types" in parameters:
        kwargs["types"] = {"sum"}
    result = statistics_during_period(
        hass,
        start,
        end,
        [entity_id],
        "hour",
        **kwargs,
    )
    return result or {}
