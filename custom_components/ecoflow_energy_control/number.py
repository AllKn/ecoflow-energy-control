"""Number controls for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import APP_NAME, CONF_POWERSTREAMS, DOMAIN, LEGACY_DASHBOARD_OBJECT_PREFIX
from .coordinator import EcoFlowEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = [
        ThresholdNumber(coordinator, "export_watts", "teruglever doel", 0, 1600, 10, UnitOfPower.WATT),
        ThresholdNumber(coordinator, "self_use_watts", "eigen gebruik doel", 0, 1600, 10, UnitOfPower.WATT),
        ThresholdNumber(coordinator, "solar_plug_threshold_watts", "laadstekkers aan vanaf gecorrigeerde zon", 0, 10000, 50, UnitOfPower.WATT),
    ]
    for device in coordinator.settings.get(CONF_POWERSTREAMS, []):
        serial = device.get("serial")
        if serial and "VUL_HIER" not in serial:
            entities.append(
                PowerStreamOutputNumber(
                    coordinator,
                    str(serial),
                    str(device.get("name") or serial),
                    float(device.get("max_watts") or 800),
                )
            )
    async_add_entities(entities)


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


class PowerStreamOutputNumber(CoordinatorEntity[EcoFlowEnergyCoordinator], NumberEntity):
    """Per-PowerStream export target."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoFlowEnergyCoordinator,
        serial: str,
        name: str,
        max_watts: float,
    ) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = "teruglevering instellen"
        self._attr_unique_id = f"{DOMAIN}_{serial}_powerstream_output_setpoint"
        self._attr_suggested_object_id = slugify(
            f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_{name}_teruglevering_instellen"
        )
        self._attr_native_min_value = 0
        self._attr_native_max_value = max(0, max_watts)
        self._attr_native_step = 10
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"ecoflow_{serial}")},
            "name": name,
            "manufacturer": "EcoFlow",
            "model": "PowerStream",
            "via_device": (DOMAIN, "controller"),
        }

    @property
    def native_value(self) -> float:
        if self._serial in self.coordinator.powerstream_targets:
            return float(self.coordinator.powerstream_targets.get(self._serial, 0))
        data = self._powerstream_data()
        return float(data.get("target_watts") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self._powerstream_data()
        return {
            "eec_device_type": "powerstream",
            "eec_sensor_role": "powerstream_setpoint",
            "serial": self._serial,
            "managed_battery_serial": data.get("battery_serial"),
            "managed_battery_name": data.get("battery_name"),
            "managed_battery_soc": data.get("battery_soc"),
            "managed_battery_free_wh": data.get("battery_free_wh"),
            "group_strategy": data.get("group_strategy"),
            "group_action": data.get("group_action"),
            "decision_reason": data.get("decision_reason"),
            "suggested_watts": data.get("suggested_watts"),
            "strategy_throttled": data.get("strategy_throttled"),
            "strategy_next_update_seconds": data.get("strategy_next_update_seconds"),
            "strategy_error": data.get("strategy_error"),
            "command_source": data.get("command_source"),
            "phase": data.get("phase"),
        }

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_powerstream_watts(self._serial, int(value))
        self.async_write_ha_state()

    def _powerstream_data(self) -> dict[str, object]:
        return (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
