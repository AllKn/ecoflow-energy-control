"""Switches for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    APP_NAME,
    CONF_DRY_RUN,
    CONF_SMART_PLUGS,
    DOMAIN,
    LEGACY_DASHBOARD_OBJECT_PREFIX,
)
from .coordinator import EcoFlowEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [DryRunSwitch(coordinator)]
    for device in coordinator.settings.get(CONF_SMART_PLUGS, []):
        serial = device.get("serial")
        if serial:
            entities.append(
                SmartPlugSwitch(coordinator, str(serial), str(device.get("name", serial)))
            )
    async_add_entities(entities)


class DryRunSwitch(CoordinatorEntity[EcoFlowEnergyCoordinator], SwitchEntity):
    """Toggle dry-run mode."""

    _attr_has_entity_name = False
    _attr_name = "testmodus"
    _attr_suggested_object_id = f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_testmodus"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_dry_run"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }

    @property
    def is_on(self) -> bool:
        return self.coordinator.dry_run

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "eec_device_type": "control",
            "eec_sensor_role": "test_mode",
        }

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.dry_run = True
        self.coordinator.settings[CONF_DRY_RUN] = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.dry_run = False
        self.coordinator.settings[CONF_DRY_RUN] = False
        self.async_write_ha_state()


class SmartPlugSwitch(CoordinatorEntity[EcoFlowEnergyCoordinator], SwitchEntity):
    """Toggle a configured Smart Plug via schema-based cloud commands."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: EcoFlowEnergyCoordinator,
        serial: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = "smart plug"
        self._attr_unique_id = f"{DOMAIN}_{serial}_smart_plug"
        self._attr_suggested_object_id = slugify(
            f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_{name}_smart_plug"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"ecoflow_{serial}")},
            "name": name,
            "manufacturer": "EcoFlow",
            "model": "Smart Plug",
            "via_device": (DOMAIN, "controller"),
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.smart_plug_last_state.get(self._serial))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        device = None
        for item in self.coordinator.settings.get(CONF_SMART_PLUGS, []):
            if str(item.get("serial")) == self._serial:
                device = item
                break
        return {
            "eec_device_type": "smart_plug",
            "eec_sensor_role": "smart_plug_control",
            "serial": self._serial,
            "schedule_enabled": device.get("schedule_enabled") if device else None,
            "schedule_on": device.get("schedule_on") if device else None,
            "schedule_off": device.get("schedule_off") if device else None,
            "last_command": self.coordinator.smart_plug_last_state.get(self._serial),
            "last_command_at": self.coordinator.smart_plug_last_state_at.get(self._serial),
        }

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_smart_plug(self._serial, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_smart_plug(self._serial, False)
        self.async_write_ha_state()
