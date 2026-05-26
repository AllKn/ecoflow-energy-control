"""EcoFlow Energy Control integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_change

from .const import (
    ATTR_SERIAL,
    ATTR_ON,
    ATTR_WATTS,
    CONF_BATTERIES,
    CONF_HOMEWIZARD_METERS,
    CONF_POWERSTREAMS,
    CONF_PRICE_SOURCE,
    CONF_PRICE_URL,
    CONF_SMA_INVERTERS,
    CONF_SMART_PLUGS,
    DEFAULT_PRICE_SOURCE,
    DOMAIN,
    SERVICE_APPLY_STRATEGY,
    SERVICE_SET_SMART_PLUG,
    SERVICE_SET_POWERSTREAM_WATTS,
)
from .coordinator import EcoFlowEnergyCoordinator

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

    async def set_powerstream_watts(call: ServiceCall) -> None:
        await coordinator.async_set_powerstream_watts(
            call.data[ATTR_SERIAL], int(call.data[ATTR_WATTS])
        )

    async def apply_strategy(call: ServiceCall) -> None:
        await coordinator.async_apply_strategy()

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
    merged.setdefault(CONF_PRICE_SOURCE, DEFAULT_PRICE_SOURCE)
    if merged != entry.data or entry.options:
        hass.config_entries.async_update_entry(entry, data=merged, options={})
