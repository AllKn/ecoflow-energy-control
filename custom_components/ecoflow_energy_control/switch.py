"""Switches for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EcoFlowEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DryRunSwitch(coordinator)])


class DryRunSwitch(CoordinatorEntity[EcoFlowEnergyCoordinator], SwitchEntity):
    """Toggle dry-run mode."""

    _attr_has_entity_name = True
    _attr_name = "testmodus"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_dry_run"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": "EcoFlow Energy Control Applicatie",
        }

    @property
    def is_on(self) -> bool:
        return self.coordinator.dry_run

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.dry_run = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.dry_run = False
        self.async_write_ha_state()
