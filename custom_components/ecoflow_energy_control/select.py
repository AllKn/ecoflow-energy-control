"""Select controls for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import APP_NAME, CONF_POWERSTREAMS, DOMAIN, POWERSTREAM_STRATEGIES, STRATEGIES
from .coordinator import EcoFlowEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SelectEntity] = [StrategySelect(coordinator)]
    for device in coordinator.settings.get(CONF_POWERSTREAMS, []):
        serial = device.get("serial")
        if serial and "VUL_HIER" not in serial:
            entities.append(
                PowerStreamStrategySelect(
                    coordinator, str(serial), str(device.get("name") or serial)
                )
            )
    async_add_entities(entities)


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
            "name": APP_NAME,
        }

    @property
    def current_option(self) -> str:
        return self.coordinator.strategy

    async def async_select_option(self, option: str) -> None:
        if option in STRATEGIES:
            self.coordinator.strategy = option
            self.async_write_ha_state()


class PowerStreamStrategySelect(CoordinatorEntity[EcoFlowEnergyCoordinator], SelectEntity):
    """Per-PowerStream strategy selector."""

    _attr_has_entity_name = True
    _attr_options = POWERSTREAM_STRATEGIES

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = f"{name} strategie"
        self._attr_unique_id = f"{DOMAIN}_{serial}_powerstream_strategy"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"ecoflow_{serial}")},
            "name": name,
            "manufacturer": "EcoFlow",
            "model": "PowerStream",
            "via_device": (DOMAIN, "controller"),
        }

    @property
    def current_option(self) -> str:
        data = (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
        return str(
            data.get("group_strategy")
            or self.coordinator.powerstream_strategies.get(self._serial)
            or "max_self_use"
        )

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
        return {
            "eec_device_type": "powerstream",
            "eec_sensor_role": "group_strategy",
            "serial": self._serial,
            "managed_battery_name": data.get("battery_name"),
            "managed_battery_soc": data.get("battery_soc"),
            "suggested_watts": data.get("suggested_watts"),
            "action": data.get("group_action"),
        }

    async def async_select_option(self, option: str) -> None:
        if option in POWERSTREAM_STRATEGIES:
            self.coordinator.set_powerstream_strategy(self._serial, option)
            self.async_write_ha_state()
