"""Number controls for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import APP_NAME, DOMAIN
from .coordinator import EcoFlowEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ThresholdNumber(coordinator, "export_watts", "teruglever doel", 0, 1600, 10, UnitOfPower.WATT),
            ThresholdNumber(coordinator, "self_use_watts", "eigen gebruik doel", 0, 1600, 10, UnitOfPower.WATT),
            ThresholdNumber(coordinator, "solar_plug_threshold_watts", "laadstekkers aan vanaf gecorrigeerde zon", 0, 10000, 50, UnitOfPower.WATT),
        ]
    )


class ThresholdNumber(CoordinatorEntity[EcoFlowEnergyCoordinator], NumberEntity):
    """Runtime numeric setting."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoFlowEnergyCoordinator,
        attr: str,
        name: str,
        minimum: float,
        maximum: float,
        step: float,
        unit: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr = attr
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{attr}"
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }

    @property
    def native_value(self) -> float:
        return getattr(self.coordinator, self._attr)

    async def async_set_native_value(self, value: float) -> None:
        setattr(self.coordinator, self._attr, value)
        self.async_write_ha_state()
