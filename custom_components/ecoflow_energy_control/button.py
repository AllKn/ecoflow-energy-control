"""Buttons for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    APP_NAME,
    CONF_POWERSTREAMS,
    CONF_SMART_PLUGS,
    DOMAIN,
    LEGACY_DASHBOARD_OBJECT_PREFIX,
)
from .coordinator import EcoFlowEnergyCoordinator
from .policy import best_scenario, scenario_is_actionable


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ApplyBestScenarioButton(coordinator),
            ApplyStrategyButton(coordinator),
            StopPowerstreamExportButton(coordinator),
            CheckEcoFlowApiButton(coordinator),
            RefreshPricesButton(coordinator),
        ]
    )


class ApplyStrategyButton(CoordinatorEntity[EcoFlowEnergyCoordinator], ButtonEntity):
    """Apply the active strategy once."""

    _attr_has_entity_name = False
    _attr_name = "strategie nu toepassen"
    _attr_suggested_object_id = (
        f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_strategie_nu_toepassen"
    )

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_apply_strategy"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }

    async def async_press(self) -> None:
        await self.coordinator.async_apply_strategy()

    @property
    def available(self) -> bool:
        return _has_configured_control_target(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "eec_device_type": "action",
            "eec_sensor_role": "apply_strategy",
            "has_powerstreams": _has_configured_powerstreams(self.coordinator),
            "has_smart_plugs": _has_configured_smart_plugs(self.coordinator),
            "last_action": (self.coordinator.data or {}).get("last_action"),
        }


class ApplyBestScenarioButton(CoordinatorEntity[EcoFlowEnergyCoordinator], ButtonEntity):
    """Apply the best simulated scenario once."""

    _attr_has_entity_name = False
    _attr_name = "advies starten"
    _attr_suggested_object_id = f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_advies_starten"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_apply_best_scenario"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }

    async def async_press(self) -> None:
        await self.coordinator.async_apply_best_scenario()

    @property
    def available(self) -> bool:
        scenario = best_scenario((self.coordinator.data or {}).get("scenarios", {}), {})
        return scenario_is_actionable(scenario)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        scenario = best_scenario((self.coordinator.data or {}).get("scenarios", {}), {})
        return {
            "eec_device_type": "action",
            "eec_sensor_role": "apply_best_scenario",
            "best_scenario": scenario.get("label") or scenario.get("key"),
            "best_scenario_key": scenario.get("key"),
            "actionable": scenario_is_actionable(scenario),
            "reason": scenario.get("reason"),
        }


class StopPowerstreamExportButton(CoordinatorEntity[EcoFlowEnergyCoordinator], ButtonEntity):
    """Stop all PowerStream export output."""

    _attr_has_entity_name = False
    _attr_name = "teruglevering naar 0"
    _attr_suggested_object_id = (
        f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_teruglevering_naar_0"
    )

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_stop_powerstream_export"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }

    async def async_press(self) -> None:
        await self.coordinator.async_stop_powerstream_export()

    @property
    def available(self) -> bool:
        return _has_configured_powerstreams(self.coordinator) and (
            _current_powerstream_export_w(self.coordinator) > 0
            or not (self.coordinator.data or {}).get("powerstreams")
        )

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "eec_device_type": "action",
            "eec_sensor_role": "stop_powerstream_export",
            "current_export_w": _current_powerstream_export_w(self.coordinator),
            "has_powerstreams": _has_configured_powerstreams(self.coordinator),
            "last_action": (self.coordinator.data or {}).get("last_action"),
        }


class CheckEcoFlowApiButton(CoordinatorEntity[EcoFlowEnergyCoordinator], ButtonEntity):
    """Manually check EcoFlow API connectivity."""

    _attr_has_entity_name = False
    _attr_name = "EcoFlow API controleren"
    _attr_suggested_object_id = (
        f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_ecoflow_api_controleren"
    )

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_check_ecoflow_api"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }

    async def async_press(self) -> None:
        await self.coordinator.async_check_ecoflow_api()

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "eec_device_type": "action",
            "eec_sensor_role": "check_ecoflow_api",
        }


class RefreshPricesButton(CoordinatorEntity[EcoFlowEnergyCoordinator], ButtonEntity):
    """Manually refresh day-ahead prices."""

    _attr_has_entity_name = False
    _attr_name = "prijzen ophalen"
    _attr_suggested_object_id = (
        f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_epex_prijzen_ophalen"
    )

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_refresh_prices"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }

    async def async_press(self) -> None:
        await self.coordinator.async_refresh_prices_now()

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "eec_device_type": "action",
            "eec_sensor_role": "refresh_prices",
        }


def _has_configured_powerstreams(coordinator: EcoFlowEnergyCoordinator) -> bool:
    return any(
        item.get("serial") and "VUL_HIER" not in str(item.get("serial"))
        for item in coordinator.settings.get(CONF_POWERSTREAMS, [])
        if isinstance(item, dict)
    )


def _has_configured_smart_plugs(coordinator: EcoFlowEnergyCoordinator) -> bool:
    return any(
        item.get("serial") and "VUL_HIER" not in str(item.get("serial"))
        for item in coordinator.settings.get(CONF_SMART_PLUGS, [])
        if isinstance(item, dict)
    )


def _has_configured_control_target(coordinator: EcoFlowEnergyCoordinator) -> bool:
    return _has_configured_powerstreams(coordinator) or _has_configured_smart_plugs(
        coordinator
    )


def _current_powerstream_export_w(coordinator: EcoFlowEnergyCoordinator) -> float:
    data = coordinator.data or {}
    try:
        return max(0.0, float(data.get("powerstream_export_w") or 0))
    except (TypeError, ValueError):
        return 0.0
