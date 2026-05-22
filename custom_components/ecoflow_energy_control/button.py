"""Buttons for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    async_add_entities([ApplyStrategyButton(coordinator)])


class ApplyStrategyButton(CoordinatorEntity[EcoFlowEnergyCoordinator], ButtonEntity):
    """Apply the active strategy once."""

    _attr_has_entity_name = True
    _attr_name = "strategie nu toepassen"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_apply_strategy"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": "EcoFlow Energy Control Applicatie",
        }

    async def async_press(self) -> None:
        await self.coordinator.async_apply_strategy()
