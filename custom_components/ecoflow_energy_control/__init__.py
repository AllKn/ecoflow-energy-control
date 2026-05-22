"""EcoFlow Energy Control integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    ATTR_SERIAL,
    ATTR_WATTS,
    DOMAIN,
    SERVICE_APPLY_STRATEGY,
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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EcoFlow Energy Control from a config entry."""
    coordinator = EcoFlowEnergyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def set_powerstream_watts(call: ServiceCall) -> None:
        await coordinator.async_set_powerstream_watts(
            call.data[ATTR_SERIAL], int(call.data[ATTR_WATTS])
        )

    async def apply_strategy(call: ServiceCall) -> None:
        await coordinator.async_apply_strategy()

    if not hass.services.has_service(DOMAIN, SERVICE_SET_POWERSTREAM_WATTS):
        hass.services.async_register(
            DOMAIN, SERVICE_SET_POWERSTREAM_WATTS, set_powerstream_watts
        )
    if not hass.services.has_service(DOMAIN, SERVICE_APPLY_STRATEGY):
        hass.services.async_register(DOMAIN, SERVICE_APPLY_STRATEGY, apply_strategy)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
