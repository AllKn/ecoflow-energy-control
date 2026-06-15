"""EcoFlow Energy Control integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_change

from .const import (
    APP_NAME,
    ATTR_SERIAL,
    ATTR_ON,
    ATTR_WATTS,
    CONF_BATTERIES,
    CONF_BATTERY_RESERVE_SOC,
    CONF_HOMEWIZARD_METERS,
    CONF_POWERSTREAMS,
    CONF_PRICE_SOURCE,
    CONF_PRICE_URL,
    CONF_SMA_INVERTERS,
    CONF_SMART_PLUGS,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_HOMEWIZARD_ROLE,
    HOMEWIZARD_ROLE_GRID_METER,
    HOMEWIZARD_ROLE_SOLAR_TOTAL,
    DOMAIN,
    SERVICE_APPLY_BEST_SCENARIO,
    SERVICE_APPLY_STRATEGY,
    SERVICE_SET_SMART_PLUG,
    SERVICE_SET_POWERSTREAM_WATTS,
    SERVICE_STOP_POWERSTREAM_EXPORT,
)
from .coordinator import EcoFlowEnergyCoordinator
from .dashboard_sync import async_sync_shipped_dashboard

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SELECT,
]

_LOGGER = logging.getLogger(__name__)
_OLD_DEFAULT_PRICE_URL = "https://epexprijzen.nl/api/v1/prices/quatt-energy/hourly"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EcoFlow Energy Control from a config entry."""
    _normalize_entry_storage(hass, entry)
    coordinator = EcoFlowEnergyCoordinator(hass, entry)
    await coordinator.async_load_simulation_state()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    entry.async_on_unload(
        async_track_time_change(
            hass,
            lambda now: hass.async_create_task(coordinator.async_daily_price_refresh()),
            hour=15,
            minute=0,
            second=0,
        )
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _shorten_legacy_entity_registry_names(hass, entry)
    await async_sync_shipped_dashboard(hass)

    async def set_powerstream_watts(call: ServiceCall) -> None:
        await coordinator.async_set_powerstream_watts(
            call.data[ATTR_SERIAL], int(call.data[ATTR_WATTS])
        )

    async def apply_strategy(call: ServiceCall) -> None:
        await coordinator.async_apply_strategy()

    async def apply_best_scenario(call: ServiceCall) -> None:
        await coordinator.async_apply_best_scenario()

    async def stop_powerstream_export(call: ServiceCall) -> None:
        await coordinator.async_stop_powerstream_export()

    async def set_smart_plug(call: ServiceCall) -> None:
        await coordinator.async_set_smart_plug(
            call.data[ATTR_SERIAL], bool(call.data[ATTR_ON])
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_POWERSTREAM_WATTS):
        hass.services.async_register(
            DOMAIN, SERVICE_SET_POWERSTREAM_WATTS, set_powerstream_watts
        )
    if not hass.services.has_service(DOMAIN, SERVICE_APPLY_STRATEGY):
        hass.services.async_register(DOMAIN, SERVICE_APPLY_STRATEGY, apply_strategy)
    if not hass.services.has_service(DOMAIN, SERVICE_APPLY_BEST_SCENARIO):
        hass.services.async_register(
            DOMAIN, SERVICE_APPLY_BEST_SCENARIO, apply_best_scenario
        )
    if not hass.services.has_service(DOMAIN, SERVICE_STOP_POWERSTREAM_EXPORT):
        hass.services.async_register(
            DOMAIN, SERVICE_STOP_POWERSTREAM_EXPORT, stop_powerstream_export
        )
    if not hass.services.has_service(DOMAIN, SERVICE_SET_SMART_PLUG):
        hass.services.async_register(DOMAIN, SERVICE_SET_SMART_PLUG, set_smart_plug)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _normalize_entry_storage(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Persist device lists from options into entry data after upgrades/reloads."""
    merged = {**entry.data, **entry.options}
    for key in (
        CONF_BATTERIES,
        CONF_POWERSTREAMS,
        CONF_SMA_INVERTERS,
        CONF_SMART_PLUGS,
        CONF_HOMEWIZARD_METERS,
    ):
        merged.setdefault(key, [])
    if merged.get(CONF_PRICE_URL) == _OLD_DEFAULT_PRICE_URL:
        merged[CONF_PRICE_URL] = ""
        merged[CONF_PRICE_SOURCE] = DEFAULT_PRICE_SOURCE
    merged[CONF_BATTERIES] = _normalize_battery_settings(
        merged.get(CONF_BATTERIES, [])
    )
    try:
        merged[CONF_HOMEWIZARD_METERS] = _prune_homewizard_manual_duplicates(
            merged.get(CONF_HOMEWIZARD_METERS, [])
        )
    except (TypeError, KeyError, ValueError) as err:
        _LOGGER.warning(
            "Ignoring invalid HomeWizard meter config during startup: %s", err
        )
        merged[CONF_HOMEWIZARD_METERS] = []
    merged.setdefault(CONF_PRICE_SOURCE, DEFAULT_PRICE_SOURCE)
    if merged != entry.data or entry.options:
        hass.config_entries.async_update_entry(entry, data=merged, options={})


def _normalize_battery_settings(items: list[dict[str, Any]] | Any) -> list[dict[str, Any]]:
    """Backfill safe battery defaults introduced after first setup."""
    if not isinstance(items, list):
        return []
    output: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        output.append(
            {
                **item,
                CONF_BATTERY_RESERVE_SOC: _coerce_reserve_soc(
                    item.get(CONF_BATTERY_RESERVE_SOC)
                ),
            }
        )
    return output


def _coerce_reserve_soc(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = DEFAULT_BATTERY_RESERVE_SOC
    return max(0, min(100, number))


def _prune_homewizard_manual_duplicates(items: list[dict[str, Any]] | Any) -> list[dict[str, Any]]:
    """Keep manual HomeWizard entries only when they don't shadow HA-imported roles."""
    if not isinstance(items, list):
        return []
    ha_roles: set[str] = set()
    seen_ha: set[str] = set()
    output: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("source") != "homeassistant":
            continue
        role = _coerce_homewizard_role(item)
        ha_roles.add(role)
        key = f"{role}:{item.get('device_id', '')}"
        if key in seen_ha:
            continue
        seen_ha.add(key)
        output.append({**item, "role": role})

    for item in items:
        if not isinstance(item, dict) or item.get("source") == "homeassistant":
            continue
        role = _coerce_homewizard_role(item)
        if role in ha_roles:
            continue
        output.append({**item, "role": role})
    return output


def _coerce_homewizard_role(item: dict[str, Any]) -> str:
    explicit = str(item.get("role") or "").strip()
    homewizard_role_solar_total = globals().get(
        "HOMEWIZARD_ROLE_SOLAR_TOTAL", "solar_total"
    )
    homewizard_role_grid_meter = globals().get("HOMEWIZARD_ROLE_GRID_METER", "grid_meter")
    if item.get("source") == "homeassistant" and _looks_like_homewizard_p1(item):
        return homewizard_role_grid_meter
    if explicit in (
        homewizard_role_solar_total,
        homewizard_role_grid_meter,
    ):
        return explicit
    return _infer_homewizard_role_from_text(
        item.get("name"),
        item.get("model"),
        item.get("host"),
        item.get("device_id"),
    )


def _looks_like_homewizard_p1(item: dict[str, Any]) -> bool:
    """Return true when a Home Assistant HomeWizard item is clearly a P1 meter."""
    entities = item.get("entities") if isinstance(item.get("entities"), dict) else {}
    if any(
        entities.get(key)
        for key in (
            "energy_import",
            "energy_import_t1",
            "energy_import_t2",
            "energy_export",
            "energy_export_t1",
            "energy_export_t2",
        )
    ):
        return True
    if entities.get("power") and any(
        entities.get(key) for key in ("power_l1", "power_l2", "power_l3")
    ):
        return True
    return (
        _infer_homewizard_role_from_text(
            item.get("name"),
            item.get("model"),
            item.get("host"),
            item.get("device_id"),
            " ".join(str(value) for value in entities.values()),
        )
        == globals().get("HOMEWIZARD_ROLE_GRID_METER", "grid_meter")
    )


def _infer_homewizard_role_from_text(*parts: Any) -> str:
    text = " ".join(str(part or "") for part in parts).lower()
    compact = text.replace("_", " ").replace("-", " ")
    if "p1" in compact or "netmeter" in compact or "energy socket" in compact:
        return globals().get("HOMEWIZARD_ROLE_GRID_METER", "grid_meter")
    if "p1 meter" in compact or "p1meter" in compact:
        return globals().get("HOMEWIZARD_ROLE_GRID_METER", "grid_meter")
    return globals().get("HOMEWIZARD_ROLE_SOLAR_TOTAL", DEFAULT_HOMEWIZARD_ROLE)


def _shorten_legacy_entity_registry_names(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Remove old long app labels from stored entity registry names."""
    registry = er.async_get(hass)
    for entity in list(registry.entities.values()):
        if entity.platform != DOMAIN or entity.config_entry_id != entry.entry_id:
            continue
        name = getattr(entity, "name", None)
        short_name = _short_legacy_entity_name(name)
        if short_name:
            registry.async_update_entity(entity.entity_id, name=short_name)


def _short_legacy_entity_name(name: str | None) -> str | None:
    """Return a short replacement for old default entity names."""
    if not name:
        return None
    prefixes = (
        "EcoFlow Energy Control applicatie",
        "Ecoflow Energy Control applicatie",
        "ecoflow energy control applicatie",
    )
    for prefix in prefixes:
        if name.startswith(prefix):
            suffix = name[len(prefix) :].strip()
            if not suffix:
                return APP_NAME
            return suffix[:1].upper() + suffix[1:]
    return None
