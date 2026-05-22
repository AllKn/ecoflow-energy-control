"""Select controls for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STRATEGIES
from .coordinator import EcoFlowEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StrategySelect(coordinator)])


class StrategySelect(CoordinatorEntity[EcoFlowEnergyCoordinator], SelectEntity):
    """Strategy selector."""

    _attr_has_entity_name = True
    _attr_name = "strategie"
    _attr_options = STRATEGIES

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_strategy"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": "EcoFlow Energy Control Applicatie",
        }

    @property
    def current_option(self) -> str:
        return self.coordinator.strategy

    async def async_select_option(self, option: str) -> None:
        if option in STRATEGIES:
            self.coordinator.strategy = option
            self.async_write_ha_state()
