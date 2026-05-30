"""Select controls for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    APP_NAME,
    CONF_POWERSTREAMS,
    DOMAIN,
    LEGACY_DASHBOARD_OBJECT_PREFIX,
    POWERSTREAM_STRATEGIES,
    POWERSTREAM_STRATEGY_BUFFER_50,
    POWERSTREAM_STRATEGY_IDLE,
    POWERSTREAM_STRATEGY_SELF_USE,
    POWERSTREAM_STRATEGY_TRADING,
    STRATEGIES,
    STRATEGY_BUFFER_50,
    STRATEGY_EXPORT,
    STRATEGY_IDLE,
    STRATEGY_SELF_USE,
)
from .coordinator import EcoFlowEnergyCoordinator

STRATEGY_LABELS = {
    STRATEGY_SELF_USE: "Eigen gebruik",
    STRATEGY_EXPORT: "Handelen",
    STRATEGY_BUFFER_50: "Buffer 50%",
    STRATEGY_IDLE: "Uit",
}
STRATEGY_VALUES = {label: value for value, label in STRATEGY_LABELS.items()}
STRATEGY_VALUES["Terugleveren"] = STRATEGY_EXPORT

POWERSTREAM_STRATEGY_LABELS = {
    POWERSTREAM_STRATEGY_SELF_USE: "Eigen gebruik",
    POWERSTREAM_STRATEGY_TRADING: "Handelen",
    POWERSTREAM_STRATEGY_BUFFER_50: "Buffer 50%",
    POWERSTREAM_STRATEGY_IDLE: "Uit",
}
POWERSTREAM_STRATEGY_VALUES = {
    label: value for value, label in POWERSTREAM_STRATEGY_LABELS.items()
}


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

    _attr_has_entity_name = False
    _attr_name = "strategie"
    _attr_suggested_object_id = f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_strategie"
    _attr_options = [STRATEGY_LABELS[value] for value in STRATEGIES]

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_strategy"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }

    @property
    def current_option(self) -> str:
        return STRATEGY_LABELS.get(self.coordinator.strategy, self.coordinator.strategy)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "eec_device_type": "control",
            "eec_sensor_role": "global_strategy",
            "strategy": self.coordinator.strategy,
        }

    async def async_select_option(self, option: str) -> None:
        strategy = STRATEGY_VALUES.get(option, option)
        if strategy in STRATEGIES:
            self.coordinator.strategy = strategy
            self.async_write_ha_state()


class PowerStreamStrategySelect(CoordinatorEntity[EcoFlowEnergyCoordinator], SelectEntity):
    """Per-PowerStream strategy selector."""

    _attr_has_entity_name = True
    _attr_options = [POWERSTREAM_STRATEGY_LABELS[value] for value in POWERSTREAM_STRATEGIES]

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = "strategie"
        self._attr_unique_id = f"{DOMAIN}_{serial}_powerstream_strategy"
        self._attr_suggested_object_id = slugify(
            f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_{name}_strategie"
        )
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
            POWERSTREAM_STRATEGY_LABELS.get(
                str(
                    data.get("group_strategy")
                    or self.coordinator.powerstream_strategies.get(self._serial)
                    or POWERSTREAM_STRATEGY_SELF_USE
                ),
                POWERSTREAM_STRATEGY_LABELS[POWERSTREAM_STRATEGY_SELF_USE],
            )
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
            "managed_battery_free_wh": data.get("battery_free_wh"),
            "suggested_watts": data.get("suggested_watts"),
            "action": data.get("group_action"),
            "decision_reason": data.get("decision_reason"),
            "strategy_throttled": data.get("strategy_throttled"),
            "strategy_next_update_seconds": data.get("strategy_next_update_seconds"),
            "strategy_error": data.get("strategy_error"),
        }

    async def async_select_option(self, option: str) -> None:
        strategy = POWERSTREAM_STRATEGY_VALUES.get(option, option)
        if strategy in POWERSTREAM_STRATEGIES:
            self.coordinator.set_powerstream_strategy(self._serial, strategy)
            self.async_write_ha_state()
