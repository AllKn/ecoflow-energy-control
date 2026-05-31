"""Buttons for EcoFlow Energy Control."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import APP_NAME, DOMAIN, LEGACY_DASHBOARD_OBJECT_PREFIX
from .coordinator import EcoFlowEnergyCoordinator


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
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "eec_device_type": "action",
            "eec_sensor_role": "apply_strategy",
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
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "eec_device_type": "action",
            "eec_sensor_role": "apply_best_scenario",
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
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "eec_device_type": "action",
            "eec_sensor_role": "stop_powerstream_export",
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
