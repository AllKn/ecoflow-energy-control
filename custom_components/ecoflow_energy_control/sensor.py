"""Sensors for EcoFlow Energy Control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    APP_NAME,
    APP_VERSION,
    DOMAIN,
    HOMEWIZARD_ROLE_GRID_METER,
    LEGACY_DASHBOARD_OBJECT_PREFIX,
    POWERSTREAM_STRATEGY_MIN_INTERVAL_SECONDS,
    STRATEGY_BUFFER_50,
    STRATEGY_EXPORT,
    STRATEGY_IDLE,
    STRATEGY_SELF_USE,
)
from .coordinator import EcoFlowEnergyCoordinator
from .health import (
    dashboard_readiness,
    live_missing_summary,
    next_user_step,
    setup_state,
    simple_flow_stage,
    source_summary,
)
from .power import normalize_live_power_w
from .policy import (
    best_scenario,
    flow_ready_state,
    flow_snapshot_icon,
    flow_snapshot_phase,
    flow_snapshot_state,
    next_dashboard_action,
    powerstream_group_decision,
    scenario_choice_summary,
    scenario_execution_hint,
    scenario_execution_state,
    scenario_is_actionable,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        VersionSensor(coordinator),
        PriceSensor(coordinator),
        PriceMinimumSensor(coordinator),
        PriceMaximumSensor(coordinator),
        CheapBandSensor(coordinator),
        ExpensiveBandSensor(coordinator),
        TotalSolarPowerSensor(coordinator),
        HomeWizardSolarPowerSensor(coordinator),
        HomeWizardGridPowerSensor(coordinator),
        HomeWizardGridStatusSensor(coordinator),
        CorrectedSolarPowerSensor(coordinator),
        CorrectedGridFlowSensor(coordinator),
        PowerStreamExportSensor(coordinator),
        WeatherNowSensor(coordinator),
        WeatherIconSummarySensor(coordinator),
        WeatherSolarForecastSensor(coordinator, 4),
        WeatherSolarForecastSensor(coordinator, 12),
        WeatherSolarForecastSensor(coordinator, 24),
        ExpectedSavingsSensor(coordinator),
        BatteryFleetSocSensor(coordinator),
        BatteryFleetAvailableEnergySensor(coordinator),
        BatteryFleetFreeEnergySensor(coordinator),
        BatteryFleetAvailableValueSensor(coordinator),
        BatteryFleetFreeValueSensor(coordinator),
        BatteryFleetChargePowerSensor(coordinator),
        BatteryFleetDischargePowerSensor(coordinator),
        BatteryFleetNetPowerSensor(coordinator),
        BestScenarioSensor(coordinator),
        ScenarioAlignmentSensor(coordinator),
        ScenarioChoiceSummarySensor(coordinator),
        StrategyGuideSensor(coordinator),
        DecisionContextSensor(coordinator),
        DashboardMainSummarySensor(coordinator),
        FlowReadySensor(coordinator),
        FlowSnapshotSensor(coordinator),
        FlowPhaseSensor(coordinator),
        FlowSummarySensor(coordinator),
        FlowValueRateSensor(coordinator),
        FlowBestPowerSensor(coordinator),
        FlowBestDayValueSensor(coordinator),
        FlowBestPeriodValueSensor(coordinator),
        FlowScenarioOverviewSensor(coordinator),
        FlowScenarioPlanSensor(coordinator),
        FlowScenarioInputSensor(coordinator),
        FlowConfidenceScoreSensor(coordinator),
        FlowConfidenceReasonSensor(coordinator),
        FlowChoiceDeltaSensor(coordinator),
        FlowChoiceStateSensor(coordinator),
        FlowStartStateSensor(coordinator),
        FlowAutoModeSensor(coordinator),
        FlowControlVerdictSensor(coordinator),
        FlowExecutionPlanSensor(coordinator),
        FlowMeasurementStateSensor(coordinator),
        FlowNextCommandSensor(coordinator),
        FlowActionStateSensor(coordinator),
        FlowCommandDeltaSensor(coordinator),
        FlowCommandNeededSensor(coordinator),
        FlowStartReasonSensor(coordinator),
        DashboardEnergyFlowSensor(coordinator),
        DashboardOverviewSensor(coordinator),
        DashboardSetupSensor(coordinator),
        DashboardSetupProgressSensor(coordinator),
        DashboardSetupAdviceSensor(coordinator),
        DashboardSourceSummarySensor(coordinator),
        DashboardProblemSensor(coordinator),
        DashboardLiveProofSensor(coordinator),
        DashboardLiveValidationSensor(coordinator),
        DashboardReadinessSensor(coordinator),
        DashboardReadinessScoreSensor(coordinator),
        DashboardInsightStateSensor(coordinator),
        DashboardNextStepSensor(coordinator),
        DashboardCheckSensor(coordinator, "prices", "prijzen"),
        DashboardCheckSensor(coordinator, "batteries", "batterijen"),
        DashboardCheckSensor(coordinator, "powerstreams", "PowerStreams"),
        DashboardCheckSensor(coordinator, "solar", "netto opwek"),
        DashboardCheckSensor(coordinator, "p1_history", "P1 historie"),
        DashboardCheckSensor(coordinator, "weather", "weer"),
        DashboardCheckSensor(coordinator, "scenarios", "scenario's"),
        DashboardCheckSensor(coordinator, "execution", "sturing"),
        StatusSensor(coordinator),
        ExecutionStatusSensor(coordinator),
        LastActionSensor(coordinator),
    ]
    for scenario_key, label in SCENARIOS.items():
        entities.extend(
            [
                ScenarioActionSensor(coordinator, scenario_key, label),
                ScenarioReasonSensor(coordinator, scenario_key, label),
                ScenarioExecutionSensor(coordinator, scenario_key, label),
                ScenarioPowerSensor(coordinator, scenario_key, label),
                ScenarioMoneyRateSensor(coordinator, scenario_key, label),
                ScenarioTotalSensor(coordinator, scenario_key, label, "day", "vandaag"),
                ScenarioTotalSensor(coordinator, scenario_key, label, "week", "deze week"),
                ScenarioTotalSensor(coordinator, scenario_key, label, "month", "deze maand"),
            ]
        )
    for device in coordinator.settings.get("batteries", []):
        serial = device.get("serial")
        if serial and "VUL_HIER" not in serial:
            name = device.get("name", serial)
            entities.extend(
                [
                    EcoFlowDeviceStatusSensor(coordinator, serial, name, "battery"),
                    BatterySocSensor(coordinator, serial, name),
                    BatteryAvailableEnergySensor(coordinator, serial, name),
                    BatteryAvailableValueSensor(coordinator, serial, name),
                    BatteryChargePowerSensor(coordinator, serial, name),
                    BatteryChargeSourceSensor(coordinator, serial, name),
                    BatteryDischargePowerSensor(coordinator, serial, name),
                    BatteryNetPowerSensor(coordinator, serial, name),
                    BatteryModeSensor(coordinator, serial, name),
                ]
            )
    for device in coordinator.settings.get("powerstreams", []):
        serial = device.get("serial")
        if serial and "VUL_HIER" not in serial:
            name = device.get("name", serial)
            entities.extend(
                [
                    EcoFlowDeviceStatusSensor(coordinator, serial, name, "powerstream"),
                    PowerStreamTargetSensor(coordinator, serial, name),
                    PowerStreamModeSensor(coordinator, serial, name),
                    PowerStreamGroupSuggestedPowerSensor(coordinator, serial, name),
                    PowerStreamGroupDeltaPowerSensor(coordinator, serial, name),
                    PowerStreamGroupCommandStatusSensor(coordinator, serial, name),
                    PowerStreamGroupBatterySocSensor(coordinator, serial, name),
                    PowerStreamGroupAvailableEnergySensor(coordinator, serial, name),
                    PowerStreamGroupFreeEnergySensor(coordinator, serial, name),
                    PowerStreamGroupActionSensor(coordinator, serial, name),
                ]
            )
    for device in coordinator.settings.get("smart_plugs", []):
        serial = device.get("serial")
        if serial and "VUL_HIER" not in serial:
            name = device.get("name", serial)
            entities.append(EcoFlowDeviceStatusSensor(coordinator, serial, name, "smart_plug"))
    for device in coordinator.settings.get("homewizard_meters", []):
        host = device.get("host") or device.get("device_id")
        if host:
            name = device.get("name", host)
            entities.extend(
                [
                    HomeWizardMeterStatusSensor(coordinator, host, name),
                    HomeWizardMeterPowerSensor(coordinator, host, name),
                    HomeWizardMeterPhasePowerSensor(coordinator, host, name, "l1"),
                    HomeWizardMeterPhasePowerSensor(coordinator, host, name, "l2"),
                    HomeWizardMeterPhasePowerSensor(coordinator, host, name, "l3"),
                    HomeWizardP1HistorySensor(coordinator, host, name, "today", "vandaag"),
                    HomeWizardP1HistorySensor(coordinator, host, name, "week", "week"),
                    HomeWizardP1HistorySensor(coordinator, host, name, "month", "maand"),
                ]
            )
    async_add_entities(entities)


class BaseSensor(CoordinatorEntity[EcoFlowEnergyCoordinator], SensorEntity):
    """Base sensor."""

    _attr_has_entity_name = False

    def __init__(self, coordinator: EcoFlowEnergyCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "controller")},
            "name": APP_NAME,
        }
        self._attr_name = name
        self._attr_suggested_object_id = slugify(
            f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_{name}"
        )


SCENARIOS = {
    "self_use": "Eigen gebruik",
    "trading": "Handelen",
    "buffer_50": "Buffer 50%",
}


class PriceSensor(BaseSensor):
    """Current spot price sensor."""

    entity_description = SensorEntityDescription(
        key="price_now", native_unit_of_measurement="EUR/kWh"
    )

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "price_now", "stroomprijs nu")

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("price_now")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        summary = data.get("price_summary") or {}
        bands = data.get("price_bands") or {}
        return {
            "eec_device_type": "price",
            "eec_sensor_role": "price_now",
            "prices": summary.get("chart", []),
            "price_count": len(summary.get("chart", [])),
            "raw_price_count": len(data.get("prices", [])),
            "price_error": (data.get("errors") or {}).get("prices"),
            "cheap_band": bands.get("cheap"),
            "expensive_band": bands.get("expensive"),
            "minimum": summary.get("min"),
            "minimum_start": summary.get("min_start"),
            "maximum": summary.get("max"),
            "maximum_start": summary.get("max_start"),
            "basis": "prijsgrenzen komen uit komende prijsuren",
        }


class VersionSensor(BaseSensor):
    """Loaded integration version."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "version", "versie")

    @property
    def native_value(self) -> str:
        return APP_VERSION

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "control",
            "eec_sensor_role": "app_version",
        }


class PriceMinimumSensor(BaseSensor):
    """Lowest upcoming electricity price."""

    _attr_native_unit_of_measurement = "EUR/kWh"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "price_minimum", "laagste prijs tot morgen")

    @property
    def native_value(self) -> float | None:
        return ((self.coordinator.data or {}).get("price_summary") or {}).get("min")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        summary = (self.coordinator.data or {}).get("price_summary") or {}
        return {
            "eec_device_type": "price",
            "eec_sensor_role": "price_minimum",
            "start": summary.get("min_start"),
            "prices": summary.get("chart", []),
            "price_count": len(summary.get("chart", [])),
            "maximum": summary.get("max"),
            "maximum_start": summary.get("max_start"),
        }


class PriceMaximumSensor(BaseSensor):
    """Highest upcoming electricity price."""

    _attr_native_unit_of_measurement = "EUR/kWh"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "price_maximum", "hoogste prijs tot morgen")

    @property
    def native_value(self) -> float | None:
        return ((self.coordinator.data or {}).get("price_summary") or {}).get("max")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        summary = (self.coordinator.data or {}).get("price_summary") or {}
        return {
            "eec_device_type": "price",
            "eec_sensor_role": "price_maximum",
            "start": summary.get("max_start"),
            "prices": summary.get("chart", []),
            "price_count": len(summary.get("chart", [])),
            "minimum": summary.get("min"),
            "minimum_start": summary.get("min_start"),
        }


class TotalSolarPowerSensor(BaseSensor):
    """Total SMA AC power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "sma_total_power", "SMA totaal vermogen")

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("solar_power") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "solar",
            "eec_sensor_role": "sma_total_power",
        }


class HomeWizardSolarPowerSensor(BaseSensor):
    """Raw HomeWizard solar power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "homewizard_solar_power", "HomeWizard opwek ruw")

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("homewizard_solar_power") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "solar",
            "eec_sensor_role": "homewizard_raw_power",
        }


class HomeWizardGridPowerSensor(BaseSensor):
    """Raw HomeWizard P1/grid power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "homewizard_grid_power", "netverbruik P1")

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("homewizard_grid_power") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "eec_device_type": "solar",
            "eec_sensor_role": "grid_power",
            "corrected_grid_power": data.get("corrected_grid_power"),
            "corrected_grid_phase_power": data.get("corrected_grid_phase_power"),
            "meaning": "positief is verbruik van net; negatief is levering aan net",
        }


class HomeWizardGridStatusSensor(BaseSensor):
    """Visible status for the optional HomeWizard P1/grid meter."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "homewizard_grid_status", "P1 status")

    @property
    def native_value(self) -> str:
        status = _homewizard_grid_status(self.coordinator)
        return str(status.get("state"))

    @property
    def icon(self) -> str:
        return {
            "P1 ok": "mdi:meter-electric",
            "P1 wacht": "mdi:meter-electric-outline",
            "P1 ontbreekt": "mdi:meter-electric-off",
        }.get(self.native_value, "mdi:meter-electric-outline")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "solar",
            "eec_sensor_role": "grid_status",
            **_homewizard_grid_status(self.coordinator),
        }


class CorrectedSolarPowerSensor(BaseSensor):
    """Solar power after subtracting controlled PowerStream export."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(
            coordinator, "corrected_solar_power", "opwek gecorrigeerd"
        )

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("corrected_solar_power") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "eec_device_type": "solar",
            "eec_sensor_role": "corrected_power",
            "raw_homewizard_solar_w": data.get("homewizard_solar_power"),
            "battery_export_subtracted_w": data.get("powerstream_export_w"),
            "meaning": "positief is netto opwek, negatief is netto verbruik",
            "corrected_phase_power": data.get("corrected_phase_power"),
        }


class CorrectedGridFlowSensor(BaseSensor):
    """Readable grid direction based on corrected HomeWizard power."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "corrected_grid_flow", "netrichting")

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        value = data.get("corrected_grid_power")
        if value is None:
            value = data.get("corrected_solar_power")
        value = float(value or 0)
        if value < -20:
            return "levering aan net"
        if value > 20:
            return "verbruik van net"
        return "neutraal"

    @property
    def icon(self) -> str:
        return {
            "levering aan net": "mdi:transmission-tower-export",
            "verbruik van net": "mdi:transmission-tower-import",
            "neutraal": "mdi:transmission-tower",
        }.get(self.native_value, "mdi:transmission-tower")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "eec_device_type": "solar",
            "eec_sensor_role": "grid_flow_state",
            "grid_power_w": data.get("homewizard_grid_power"),
            "corrected_grid_power_w": data.get("corrected_grid_power"),
            "corrected_power_w": data.get("corrected_solar_power"),
            "raw_homewizard_solar_w": data.get("homewizard_solar_power"),
            "battery_export_subtracted_w": data.get("powerstream_export_w"),
            "meaning": "positief is verbruik van net; negatief is levering aan net",
        }


class PowerStreamExportSensor(BaseSensor):
    """Tracked PowerStream export controlled by this integration."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(
            coordinator, "powerstream_export_w", "PowerStream teruglevering"
        )

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("powerstream_export_w") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "solar",
            "eec_sensor_role": "powerstream_export",
        }


class WeatherNowSensor(BaseSensor):
    """Current weather summary."""

    _attr_native_unit_of_measurement = "W/m²"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "weather_solar_now", "zon nu")

    @property
    def native_value(self) -> float:
        return float(((self.coordinator.data or {}).get("weather") or {}).get("shortwave_w_m2") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        weather = ((self.coordinator.data or {}).get("weather") or {})
        return {
            "eec_device_type": "weather",
            "eec_sensor_role": "weather_now",
            "city": weather.get("city"),
            "provider": weather.get("provider"),
            "temperature": weather.get("temperature"),
            "cloud_cover": weather.get("cloud_cover"),
            "weather_icon": weather.get("weather_icon"),
            "weather_label": weather.get("weather_label"),
            "icon_summary": weather.get("icon_summary"),
            "hourly": weather.get("hourly", []),
        }


class WeatherSolarForecastSensor(BaseSensor):
    """Expected solar radiation for a horizon."""

    _attr_native_unit_of_measurement = "Wh/kWp"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator, hours: int) -> None:
        super().__init__(coordinator, f"weather_solar_{hours}h", f"zon {hours} uur")
        self._hours = hours

    @property
    def native_value(self) -> float:
        weather = (self.coordinator.data or {}).get("weather") or {}
        return float(weather.get(f"solar_next_{self._hours}h_wh_kwp") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        weather = (self.coordinator.data or {}).get("weather") or {}
        hourly = weather.get("hourly", [])
        return {
            "eec_device_type": "weather",
            "eec_sensor_role": f"weather_solar_{self._hours}h",
            "city": weather.get("city"),
            "provider": weather.get("provider"),
            "horizon_hours": self._hours,
            "weather_label": weather.get("weather_label"),
            "weather_icon": weather.get("weather_icon"),
            "icon_summary": weather.get("icon_summary"),
            "temperature": weather.get("temperature"),
            "cloud_cover": weather.get("cloud_cover"),
            "hourly": hourly[: self._hours],
            "unit_note": "verwachte Wh per kWp opgesteld vermogen",
        }


class WeatherIconSummarySensor(BaseSensor):
    """Compact icon timeline for the next weather hours."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "weather_icon_summary", "komende uren")

    @property
    def native_value(self) -> str:
        weather = (self.coordinator.data or {}).get("weather") or {}
        return str(weather.get("icon_summary") or "geen weerdata")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        weather = (self.coordinator.data or {}).get("weather") or {}
        return {
            "eec_device_type": "weather",
            "eec_sensor_role": "weather_icon_summary",
            "city": weather.get("city"),
            "provider": weather.get("provider"),
            "horizon_hours": 24,
            "weather_label": weather.get("weather_label"),
            "weather_icon": weather.get("weather_icon"),
            "hourly": (weather.get("hourly") or [])[:24],
        }


class ExpectedSavingsSensor(BaseSensor):
    """Expected savings based on 24h solar forecast and current price."""

    _attr_native_unit_of_measurement = "EUR/kWp"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "expected_savings_24h", "verwachte besparing")

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("expected_savings_eur") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        weather = (self.coordinator.data or {}).get("weather") or {}
        return {
            "eec_device_type": "weather",
            "eec_sensor_role": "expected_savings",
            "horizon": "24h",
            "basis": "per kWp, op huidige stroomprijs",
            "solar_24h_wh_kwp": weather.get("solar_next_24h_wh_kwp"),
            "price_now": (self.coordinator.data or {}).get("price_now"),
        }


class BatteryFleetSocSensor(BaseSensor):
    """Weighted SoC for all configured EcoFlow batteries."""

    _attr_native_unit_of_measurement = "%"
    _attr_device_class = "battery"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "battery_fleet_soc", "accu totaal")

    @property
    def native_value(self) -> float:
        summary = _battery_fleet_summary(self.coordinator)
        return round(summary["soc"], 1) if summary["capacity_kwh"] else 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            **_fleet_attrs("battery_fleet_soc"),
            **_battery_fleet_summary(self.coordinator),
        }


class BatteryFleetAvailableEnergySensor(BaseSensor):
    """Available energy for all configured EcoFlow batteries."""

    _attr_native_unit_of_measurement = "kWh"
    _attr_device_class = "energy"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "battery_fleet_available_kwh", "accu beschikbaar")

    @property
    def native_value(self) -> float:
        return _battery_fleet_summary(self.coordinator)["available_kwh"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            **_fleet_attrs("battery_fleet_available_kwh"),
            **_battery_fleet_summary(self.coordinator),
        }


class BatteryFleetFreeEnergySensor(BaseSensor):
    """Remaining storage space for all configured EcoFlow batteries."""

    _attr_native_unit_of_measurement = "kWh"
    _attr_device_class = "energy"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "battery_fleet_free_kwh", "accu ruimte")

    @property
    def native_value(self) -> float:
        return _battery_fleet_summary(self.coordinator)["free_kwh"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            **_fleet_attrs("battery_fleet_free_kwh"),
            **_battery_fleet_summary(self.coordinator),
        }


class BatteryFleetAvailableValueSensor(BaseSensor):
    """Current value of all available battery energy."""

    _attr_native_unit_of_measurement = "EUR"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "battery_fleet_available_eur", "accu waarde")

    @property
    def native_value(self) -> float:
        price = (self.coordinator.data or {}).get("price_now")
        if price is None:
            return 0.0
        return round(
            _battery_fleet_summary(self.coordinator)["available_kwh"] * float(price),
            2,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        summary = _battery_fleet_summary(self.coordinator)
        return {
            **_fleet_attrs("battery_fleet_available_eur"),
            **summary,
            "price_eur_kwh": (self.coordinator.data or {}).get("price_now"),
        }


class BatteryFleetFreeValueSensor(BaseSensor):
    """Current cost to fill remaining battery space at the live price."""

    _attr_native_unit_of_measurement = "EUR"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "battery_fleet_free_eur", "ruimte waarde")

    @property
    def native_value(self) -> float:
        price = (self.coordinator.data or {}).get("price_now")
        if price is None:
            return 0.0
        return round(
            _battery_fleet_summary(self.coordinator)["free_kwh"] * float(price),
            2,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        summary = _battery_fleet_summary(self.coordinator)
        return {
            **_fleet_attrs("battery_fleet_free_eur"),
            **summary,
            "price_eur_kwh": (self.coordinator.data or {}).get("price_now"),
            "meaning": "geschatte waarde/kosten om vrije opslagruimte te vullen",
        }


class BatteryFleetChargePowerSensor(BaseSensor):
    """Combined live charging power for all configured EcoFlow batteries."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "battery_fleet_charge_power", "accu in")

    @property
    def native_value(self) -> float:
        return _battery_fleet_summary(self.coordinator)["charge_w"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            **_fleet_attrs("battery_fleet_charge_w"),
            **_battery_fleet_summary(self.coordinator),
        }


class BatteryFleetDischargePowerSensor(BaseSensor):
    """Combined live discharging power for all configured EcoFlow batteries."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "battery_fleet_discharge_power", "accu uit")

    @property
    def native_value(self) -> float:
        return _battery_fleet_summary(self.coordinator)["discharge_w"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            **_fleet_attrs("battery_fleet_discharge_w"),
            **_battery_fleet_summary(self.coordinator),
        }


class BatteryFleetNetPowerSensor(BaseSensor):
    """Combined battery flow: positive is discharge, negative is charge."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "battery_fleet_net_power", "accu netto")

    @property
    def native_value(self) -> float:
        return _battery_fleet_summary(self.coordinator)["net_w"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            **_fleet_attrs("battery_fleet_net_w"),
            **_battery_fleet_summary(self.coordinator),
            "meaning": "positief is levering uit accu; negatief is laden naar accu",
        }


class BestScenarioSensor(BaseSensor):
    """Best live scenario based on the simulated EUR/hour result."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "best_scenario", "beste scenario")

    @property
    def native_value(self) -> str:
        scenario = _best_scenario(self.coordinator)
        return scenario.get("label", "wachten")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        scenario = _best_scenario(self.coordinator)
        data = self.coordinator.data or {}
        bands = data.get("price_bands") or {}
        return {
            "eec_device_type": "scenario",
            "eec_sensor_role": "scenario_best",
            "scenario_key": scenario.get("key"),
            "action": scenario.get("action"),
            "reason": scenario.get("reason"),
            "power_w": scenario.get("power_w"),
            "eur_per_hour": scenario.get("eur_per_hour"),
            "day_eur": scenario.get("day_eur"),
            "week_eur": scenario.get("week_eur"),
            "month_eur": scenario.get("month_eur"),
            "price_now": data.get("price_now"),
            "price_cheap_band": bands.get("cheap"),
            "price_expensive_band": bands.get("expensive"),
            "corrected_solar_power": data.get("corrected_solar_power"),
        }


class ScenarioAlignmentSensor(BaseSensor):
    """Compare the selected global strategy with the best simulated scenario."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "scenario_alignment", "strategie match")

    @property
    def native_value(self) -> str:
        selected = _selected_scenario_key(self.coordinator.strategy)
        best = _best_scenario(self.coordinator).get("key")
        if selected is None:
            return "uit"
        if not best:
            return "wachten"
        return "volgt advies" if selected == best else "wijkt af"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        selected = _selected_scenario_key(self.coordinator.strategy)
        best = _best_scenario(self.coordinator)
        selected_data = (
            _scenario_data(self.coordinator, selected) if selected else {}
        )
        return {
            "eec_device_type": "scenario",
            "eec_sensor_role": "scenario_alignment",
            "selected_strategy": self.coordinator.strategy,
            "selected_scenario_key": selected,
            "selected_label": selected_data.get("label"),
            "selected_action": selected_data.get("action"),
            "selected_reason": selected_data.get("reason"),
            "selected_eur_per_hour": selected_data.get("eur_per_hour"),
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "best_action": best.get("action"),
            "best_reason": best.get("reason"),
            "best_eur_per_hour": best.get("eur_per_hour"),
        }


class ScenarioChoiceSummarySensor(BaseSensor):
    """Compact explanation of the selected scenario versus the best advice."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "scenario_choice_summary", "scenario keuze")

    @property
    def native_value(self) -> str:
        summary = _scenario_choice_summary(self.coordinator)
        return str(summary.get("summary"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "scenario",
            "eec_sensor_role": "scenario_choice_summary",
            **_scenario_choice_summary(self.coordinator),
        }


class StrategyGuideSensor(BaseSensor):
    """Short dashboard help for the available user strategies."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "strategy_guide", "strategie hulp")

    @property
    def native_value(self) -> str:
        guide = _strategy_guide(self.coordinator)
        return str(guide.get("selected_summary"))

    @property
    def icon(self) -> str:
        return "mdi:help-circle-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_strategy_guide",
            **_strategy_guide(self.coordinator),
        }


class DecisionContextSensor(BaseSensor):
    """Compact explanation of the inputs behind the current advice."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "decision_context", "waarom advies")

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        best = _best_scenario(self.coordinator)
        price_label = _price_context_label(data)
        solar_label = _solar_context_label(data.get("corrected_solar_power"))
        fleet = _battery_fleet_summary(self.coordinator)
        available = fleet.get("available_kwh")
        action = best.get("action") or "wachten"
        if available is None:
            storage = "accu onbekend"
        else:
            storage = f"{float(available):.1f} kWh"
        return f"{price_label}, {solar_label}, {storage}: {action}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        bands = data.get("price_bands") or {}
        best = _best_scenario(self.coordinator)
        fleet = _battery_fleet_summary(self.coordinator)
        solar = data.get("corrected_solar_power")
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "decision_context",
            "price_context": _price_context_label(data),
            "solar_context": _solar_context_label(solar),
            "price_now": data.get("price_now"),
            "price_cheap_band": bands.get("cheap"),
            "price_expensive_band": bands.get("expensive"),
            "corrected_solar_power": solar,
            "battery_soc": fleet.get("soc"),
            "available_kwh": fleet.get("available_kwh"),
            "free_kwh": fleet.get("free_kwh"),
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "best_action": best.get("action"),
            "best_reason": best.get("reason"),
            "best_actionable": scenario_is_actionable(best),
        }


class FlowSummarySensor(BaseSensor):
    """One-line summary of the simple control flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_flow_summary", "flow advies")

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        readiness = dashboard_readiness(data, _dashboard_settings(self.coordinator))
        if readiness.get("status") != "klaar":
            return f"actie nodig: {readiness.get('next_step', 'controleer datacheck')}"

        best = _best_scenario(self.coordinator)
        best_key = best.get("key")
        selected_key = _selected_scenario_key(self.coordinator.strategy)
        label = best.get("label") or "wachten"
        action = best.get("action") or "wachten"
        eur_per_hour = _as_float(best.get("eur_per_hour"))
        value = f"{eur_per_hour:+.2f} EUR/u" if eur_per_hour is not None else "geen EUR/u"
        actionable = scenario_is_actionable(best)
        next_action = _next_dashboard_action(self.coordinator)
        next_summary = str(next_action.get("summary") or action)

        if not actionable:
            prefix = "advies wacht"
        elif self.coordinator.dry_run:
            prefix = "testmodus"
        elif selected_key is None:
            prefix = "scenario uit"
        elif selected_key == best_key:
            prefix = "volgt advies"
        else:
            prefix = "advies wijkt af"
        return f"{prefix}: {label} - {next_summary} ({value})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        readiness = dashboard_readiness(data, _dashboard_settings(self.coordinator))
        best = _best_scenario(self.coordinator)
        selected_key = _selected_scenario_key(self.coordinator.strategy)
        selected_data = (
            _scenario_data(self.coordinator, selected_key) if selected_key else {}
        )
        fleet = _battery_fleet_summary(self.coordinator)
        actionable = scenario_is_actionable(best)
        next_action = _next_dashboard_action(self.coordinator)
        start_state = _flow_start_state(
            readiness,
            actionable,
            self.coordinator.dry_run,
        )
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_flow_summary",
            "readiness_status": readiness.get("status"),
            "readiness_score": readiness.get("score"),
            "next_step": readiness.get("next_step"),
            "test_mode": self.coordinator.dry_run,
            "selected_strategy": self.coordinator.strategy,
            "selected_scenario_key": selected_key,
            "selected_label": selected_data.get("label"),
            "selected_action": selected_data.get("action"),
            "selected_eur_per_hour": selected_data.get("eur_per_hour"),
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "best_action": best.get("action"),
            "best_reason": best.get("reason"),
            "best_eur_per_hour": best.get("eur_per_hour"),
            "best_actionable": actionable,
            "next_action": next_action.get("summary"),
            "next_action_type": next_action.get("action_type"),
            "can_execute": next_action.get("can_execute"),
            "command_required": next_action.get("command_required"),
            "start_button_state": start_state,
            "start_button_reason": _flow_start_reason(readiness, best, start_state),
            "price_now": data.get("price_now"),
            "corrected_solar_power": data.get("corrected_solar_power"),
            "battery_soc": fleet.get("soc"),
            "available_kwh": fleet.get("available_kwh"),
            "free_kwh": fleet.get("free_kwh"),
        }


class FlowValueRateSensor(BaseSensor):
    """Current expected value of the best visible scenario."""

    _attr_native_unit_of_measurement = "EUR/u"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_value_rate", "flow opbrengst")

    @property
    def native_value(self) -> float:
        best = _best_scenario(self.coordinator)
        return round(_as_float(best.get("eur_per_hour")) or 0.0, 4)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        best = _best_scenario(self.coordinator)
        selected_key = _selected_scenario_key(self.coordinator.strategy)
        selected = _scenario_data(self.coordinator, selected_key) if selected_key else {}
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_value_rate",
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "best_action": best.get("action"),
            "best_reason": best.get("reason"),
            "best_eur_per_hour": best.get("eur_per_hour"),
            "best_day_eur": best.get("day_eur"),
            "best_actionable": scenario_is_actionable(best),
            "selected_strategy": self.coordinator.strategy,
            "selected_scenario_key": selected_key,
            "selected_eur_per_hour": selected.get("eur_per_hour"),
            "delta_eur_per_hour": round(
                (_as_float(best.get("eur_per_hour")) or 0.0)
                - (_as_float(selected.get("eur_per_hour")) or 0.0),
                4,
            ),
            "price_now": data.get("price_now"),
            "corrected_solar_power": data.get("corrected_solar_power"),
            "test_mode": self.coordinator.dry_run,
        }


class FlowBestPowerSensor(BaseSensor):
    """Suggested power for the currently best scenario."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_best_power", "flow vermogen")

    @property
    def native_value(self) -> float:
        best = _best_scenario(self.coordinator)
        return round(_as_float(best.get("power_w")) or 0.0, 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        best = _best_scenario(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_best_power",
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "best_action": best.get("action"),
            "best_reason": best.get("reason"),
            "best_power_w": best.get("power_w"),
            "best_actionable": scenario_is_actionable(best),
        }


class FlowBestDayValueSensor(BaseSensor):
    """Expected current-day value for the currently best scenario."""

    _attr_native_unit_of_measurement = "EUR"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_best_day_value", "flow dagwaarde")

    @property
    def native_value(self) -> float:
        best = _best_scenario(self.coordinator)
        return round(_as_float(best.get("day_eur")) or 0.0, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        best = _best_scenario(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_best_day_value",
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "best_action": best.get("action"),
            "best_reason": best.get("reason"),
            "best_day_eur": best.get("day_eur"),
            "best_week_eur": best.get("week_eur"),
            "best_month_eur": best.get("month_eur"),
            "best_actionable": scenario_is_actionable(best),
        }


class FlowBestPeriodValueSensor(BaseSensor):
    """Compact day/week/month value for the currently best scenario."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_best_period_value", "flow totalen")

    @property
    def native_value(self) -> str:
        best = _best_scenario(self.coordinator)
        day = _as_float(best.get("day_eur")) or 0.0
        week = _as_float(best.get("week_eur")) or 0.0
        month = _as_float(best.get("month_eur")) or 0.0
        return f"D {day:+.2f} / W {week:+.2f} / M {month:+.2f}"

    @property
    def icon(self) -> str:
        best = _best_scenario(self.coordinator)
        month = _as_float(best.get("month_eur")) or 0.0
        if month > 0:
            return "mdi:cash-plus"
        if month < 0:
            return "mdi:cash-minus"
        return "mdi:cash-clock"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        best = _best_scenario(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_best_period_value",
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "best_action": best.get("action"),
            "best_reason": best.get("reason"),
            "best_day_eur": best.get("day_eur"),
            "best_week_eur": best.get("week_eur"),
            "best_month_eur": best.get("month_eur"),
            "best_actionable": scenario_is_actionable(best),
            "basis": "geschat effect van het huidige beste scenario",
        }


class FlowScenarioOverviewSensor(BaseSensor):
    """One-line scenario explanation for the main dashboard."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_scenario_overview", "scenario nu")

    @property
    def native_value(self) -> str:
        return str(_scenario_overview(self.coordinator).get("summary"))

    @property
    def icon(self) -> str:
        state = str(_scenario_overview(self.coordinator).get("state"))
        return {
            "volgt advies": "mdi:check-circle",
            "wijkt af": "mdi:swap-horizontal",
            "uit": "mdi:pause-circle",
            "data nodig": "mdi:database-alert",
            "wacht": "mdi:timer-sand",
        }.get(state, "mdi:chart-timeline-variant")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_scenario_overview",
            **_scenario_overview(self.coordinator),
        }


class FlowScenarioPlanSensor(BaseSensor):
    """Visible plain-language scenario plan for the main dashboard."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_scenario_plan", "scenario plan")

    @property
    def native_value(self) -> str:
        overview = _scenario_overview(self.coordinator)
        plan = overview.get("plan_summary") or overview.get("summary")
        hint = overview.get("execution_hint")
        if hint:
            return _state_text(f"{hint}: {plan}")
        if overview.get("execution_state") != "uitvoerbaar":
            reason = overview.get("execution_summary") or overview.get("execution_blocker")
            if reason:
                return _state_text(f"{reason}: {plan}")
        return _state_text(plan)

    @property
    def icon(self) -> str:
        state = str(_scenario_overview(self.coordinator).get("state"))
        return {
            "volgt advies": "mdi:clipboard-check",
            "wijkt af": "mdi:clipboard-alert",
            "uit": "mdi:clipboard-off",
            "data nodig": "mdi:clipboard-text-clock",
            "wacht": "mdi:clipboard-text-clock",
        }.get(state, "mdi:clipboard-text")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        overview = _scenario_overview(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_scenario_plan",
            "plan": overview.get("plan_summary"),
            "selected_plan": overview.get("selected_plan"),
            "best_plan": overview.get("best_plan"),
            "choice_state": overview.get("choice_state"),
            "choice_summary": overview.get("choice_summary"),
            "delta_eur_per_hour": overview.get("delta_eur_per_hour"),
            "execution_state": overview.get("execution_state"),
            "execution_summary": overview.get("execution_summary"),
            "execution_blocker": overview.get("execution_blocker"),
            "execution_hint": overview.get("execution_hint"),
            "next_command": overview.get("next_command"),
            "can_execute": overview.get("can_execute"),
            "command_required": overview.get("command_required"),
            "blocked_by": overview.get("blocked_by"),
            "test_mode": overview.get("test_mode"),
        }


class FlowScenarioInputSensor(BaseSensor):
    """Compact input quality for the currently best scenario."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_scenario_input", "scenario input")

    @property
    def native_value(self) -> str:
        best = _best_scenario(self.coordinator)
        if not best.get("key"):
            return "wachten"
        return "ok" if best.get("input_ready") else "beperkt"

    @property
    def icon(self) -> str:
        return {
            "ok": "mdi:database-check",
            "beperkt": "mdi:database-alert",
            "wachten": "mdi:database-clock",
        }.get(self.native_value, "mdi:database-question")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        best = _best_scenario(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_scenario_input",
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "input_ready": best.get("input_ready"),
            "input_warnings": best.get("input_warnings"),
            "best_reason": best.get("reason"),
            "price_eur_kwh": best.get("price_eur_kwh"),
            "battery_soc": best.get("battery_soc"),
            "corrected_solar_power": (self.coordinator.data or {}).get(
                "corrected_solar_power"
            ),
        }


class FlowConfidenceScoreSensor(BaseSensor):
    """Single confidence score for the current scenario advice."""

    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_confidence_score", "zekerheid")

    @property
    def native_value(self) -> int:
        return int(_scenario_confidence(self.coordinator)["score"])

    @property
    def icon(self) -> str:
        score = self.native_value
        if score >= 85:
            return "mdi:shield-check"
        if score >= 60:
            return "mdi:shield-half-full"
        return "mdi:shield-alert"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_confidence_score",
            **_scenario_confidence(self.coordinator),
        }


class FlowConfidenceReasonSensor(BaseSensor):
    """Primary reason behind the current scenario confidence score."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_confidence_reason", "zekerheid reden")

    @property
    def native_value(self) -> str:
        confidence = _scenario_confidence(self.coordinator)
        reasons = confidence.get("reasons") or []
        if reasons:
            return str(reasons[0])
        return "advies betrouwbaar"

    @property
    def icon(self) -> str:
        state = str(_scenario_confidence(self.coordinator).get("state") or "")
        return {
            "hoog": "mdi:shield-check",
            "middel": "mdi:shield-half-full",
            "laag": "mdi:shield-alert",
        }.get(state, "mdi:shield-search")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_confidence_reason",
            **_scenario_confidence(self.coordinator),
        }


class DashboardLiveValidationSensor(BaseSensor):
    """Single visible state for whether live Home Assistant proof is sufficient."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_live_validation", "live validatie")

    @property
    def native_value(self) -> str:
        return str(_live_validation(self.coordinator).get("state"))

    @property
    def icon(self) -> str:
        state = str(_live_validation(self.coordinator).get("state"))
        return {
            "live klaar": "mdi:check-decagram",
            "basis live": "mdi:lightbulb-on",
            "testmodus": "mdi:test-tube",
            "sturing beperkt": "mdi:progress-wrench",
            "optimalisatie beperkt": "mdi:tune",
            "data nodig": "mdi:database-alert",
            "actie nodig": "mdi:alert-decagram",
            "geen bewijs": "mdi:help-circle",
        }.get(state, "mdi:shield-question")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_live_validation",
            **_live_validation(self.coordinator),
        }


class FlowChoiceStateSensor(BaseSensor):
    """Compact selected-versus-advised scenario state for the top flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_choice_state", "flow keuze")

    @property
    def native_value(self) -> str:
        choice = _scenario_choice_summary(self.coordinator)
        return str(choice.get("state") or "wachten")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        choice = _scenario_choice_summary(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_choice_state",
            **choice,
            "test_mode": self.coordinator.dry_run,
        }


class FlowChoiceDeltaSensor(BaseSensor):
    """EUR/hour opportunity when selected strategy differs from best advice."""

    _attr_native_unit_of_measurement = "EUR/u"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_choice_delta", "keuze verschil")

    @property
    def native_value(self) -> float:
        choice = _scenario_choice_summary(self.coordinator)
        return round(_as_float(choice.get("delta_eur_per_hour")) or 0.0, 3)

    @property
    def icon(self) -> str:
        value = self.native_value
        if value > 0:
            return "mdi:cash-alert"
        if value < 0:
            return "mdi:cash-check"
        return "mdi:cash-sync"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        choice = _scenario_choice_summary(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_choice_delta",
            **choice,
            "basis": "positief betekent gemiste waarde t.o.v. beste scenario",
        }


class FlowReadySensor(BaseSensor):
    """Single verdict showing whether the main flow can be trusted now."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_ready_state", "flow klaar")

    @property
    def native_value(self) -> str:
        return _flow_ready_state(self.coordinator)["state"]

    @property
    def icon(self) -> str:
        return str(_flow_ready_state(self.coordinator).get("icon"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_ready_state",
            **_flow_ready_state(self.coordinator),
        }


class DashboardMainSummarySensor(BaseSensor):
    """One compact top-level summary for the main dashboard."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_main_summary", "main")

    @property
    def native_value(self) -> str:
        return str(_main_summary(self.coordinator).get("summary"))

    @property
    def icon(self) -> str:
        return str(_main_summary(self.coordinator).get("icon"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_main_summary",
            **_main_summary(self.coordinator),
        }


class FlowSnapshotSensor(BaseSensor):
    """Single dashboard snapshot for the whole simple flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_flow_snapshot", "flow overzicht")

    @property
    def native_value(self) -> str:
        snapshot = _flow_snapshot(self.coordinator)
        return str(snapshot.get("summary"))

    @property
    def icon(self) -> str:
        return str(_flow_snapshot(self.coordinator).get("snapshot_icon"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_flow_snapshot",
            **_flow_snapshot(self.coordinator),
        }


class FlowPhaseSensor(BaseSensor):
    """Compact visible phase for the simple dashboard flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_flow_phase", "flow fase")

    @property
    def native_value(self) -> str:
        return str(_flow_snapshot(self.coordinator).get("flow_phase"))

    @property
    def icon(self) -> str:
        return str(_flow_snapshot(self.coordinator).get("snapshot_icon"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_flow_phase",
            **_flow_snapshot(self.coordinator),
        }


class FlowStartStateSensor(BaseSensor):
    """Compact state for the primary advice start button."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_start_state", "startstatus")

    @property
    def native_value(self) -> str:
        readiness = dashboard_readiness(
            self.coordinator.data or {}, _dashboard_settings(self.coordinator)
        )
        best = _best_scenario(self.coordinator)
        return _flow_start_state(
            readiness,
            scenario_is_actionable(best),
            self.coordinator.dry_run,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        readiness = dashboard_readiness(data, _dashboard_settings(self.coordinator))
        best = _best_scenario(self.coordinator)
        actionable = scenario_is_actionable(best)
        state = _flow_start_state(
            readiness,
            actionable,
            self.coordinator.dry_run,
        )
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_start_state",
            "reason": _flow_start_reason(readiness, best, state),
            "best_actionable": actionable,
            "best_scenario_key": best.get("key"),
            "best_label": best.get("label"),
            "best_action": best.get("action"),
            "best_reason": best.get("reason"),
            "readiness_status": readiness.get("status"),
            "test_mode": self.coordinator.dry_run,
        }


class FlowStartReasonSensor(BaseSensor):
    """Visible reason for the primary advice start button state."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_start_reason", "startreden")

    @property
    def native_value(self) -> str:
        return str(_start_context(self.coordinator).get("reason"))

    @property
    def icon(self) -> str:
        state = str(_start_context(self.coordinator).get("state") or "")
        return {
            "startbaar": "mdi:play-circle",
            "testmodus": "mdi:flask",
            "wachten": "mdi:timer-sand",
            "actie nodig": "mdi:alert-circle",
        }.get(state, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_start_reason",
            **_start_context(self.coordinator),
        }


class FlowAutoModeSensor(BaseSensor):
    """Single state showing whether automatic control is usable now."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_auto_mode", "automodus")

    @property
    def native_value(self) -> str:
        return _auto_mode_state(self.coordinator)["state"]

    @property
    def icon(self) -> str:
        return {
            "actief": "mdi:autorenew",
            "testmodus": "mdi:flask",
            "wachten": "mdi:timer-sand",
            "uit": "mdi:pause-circle",
            "wijkt af": "mdi:swap-horizontal",
            "geblokkeerd": "mdi:alert-circle",
        }.get(self.native_value, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        auto_mode = _auto_mode_state(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_auto_mode",
            **auto_mode,
        }


class FlowControlVerdictSensor(BaseSensor):
    """One-line verdict for whether the app may control devices now."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_control_verdict", "stuuradvies")

    @property
    def native_value(self) -> str:
        return str(_control_verdict(self.coordinator).get("state") or "wachten")

    @property
    def icon(self) -> str:
        return str(_control_verdict(self.coordinator).get("icon") or "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_control_verdict",
            **_control_verdict(self.coordinator),
        }


class FlowExecutionPlanSensor(BaseSensor):
    """Concrete PowerStream execution plan for the simple dashboard flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_execution_plan", "uitvoerplan")

    @property
    def native_value(self) -> str:
        plan = _powerstream_execution_plan(self.coordinator)
        issues = _powerstream_issue_summary(plan)
        if not plan:
            return "geen PowerStreams"
        if issues["error_count"]:
            return f"fout: {issues['first_error_name']}"
        if issues["throttled_count"]:
            return f"wacht: {issues['first_throttled_name']}"
        unknown_current = [
            item
            for item in plan
            if not item.get("current_watts_known") and not item.get("command_needed")
        ]
        if unknown_current:
            return f"wacht: {len(unknown_current)} groep(en)"
        unverified_current = [
            item
            for item in plan
            if item.get("current_watts_verified") is False
            and not item.get("command_needed")
        ]
        if unverified_current:
            return f"wacht op meting: {len(unverified_current)} groep(en)"
        to_adjust = [item for item in plan if item.get("command_needed")]
        if to_adjust:
            delta = sum(float(item.get("delta_watts") or 0) for item in to_adjust)
            return f"bijsturen: {len(to_adjust)} groep(en), {delta:+.0f} W"
        active = [item for item in plan if float(item.get("suggested_watts") or 0) > 0]
        if active:
            watts = sum(float(item.get("suggested_watts") or 0) for item in active)
            return f"{len(active)} groep(en), {watts:.0f} W advies"
        return "stand-by"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        plan = _powerstream_execution_plan(self.coordinator)
        data = self.coordinator.data or {}
        issues = _powerstream_issue_summary(plan)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_execution_plan",
            "groups": plan,
            **issues,
            "group_count": len(plan),
            "active_group_count": len(
                [item for item in plan if float(item.get("suggested_watts") or 0) > 0]
            ),
            "suggested_total_w": round(
                sum(float(item.get("suggested_watts") or 0) for item in plan), 0
            ),
            "current_total_w": round(
                sum(float(item.get("current_watts") or 0) for item in plan), 0
            ),
            "delta_total_w": round(
                sum(float(item.get("delta_watts") or 0) for item in plan), 0
            ),
            "command_needed_count": len(
                [item for item in plan if item.get("command_needed")]
            ),
            "unknown_current_count": len(
                [item for item in plan if not item.get("current_watts_known")]
            ),
            "unverified_current_count": len(
                [item for item in plan if item.get("current_watts_verified") is False]
            ),
            "price_now": data.get("price_now"),
            "corrected_solar_power": data.get("corrected_solar_power"),
            "dry_run": self.coordinator.dry_run,
        }


class FlowMeasurementStateSensor(BaseSensor):
    """Compact proof that PowerStream output is based on live telemetry."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_measurement_state", "meting")

    @property
    def native_value(self) -> str:
        state = _measurement_state(self.coordinator)
        return str(state.get("state") or "onbekend")

    @property
    def icon(self) -> str:
        return {
            "gemeten": "mdi:gauge",
            "wacht meting": "mdi:gauge-empty",
            "beperkt": "mdi:gauge-low",
            "fout": "mdi:alert-circle",
            "geen PS": "mdi:power-plug-off",
            "onbekend": "mdi:gauge-empty",
        }.get(self.native_value, "mdi:gauge-empty")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_measurement_state",
            **_measurement_state(self.coordinator),
        }


class FlowCommandDeltaSensor(BaseSensor):
    """Absolute wattage difference between current and advised PowerStream output."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_command_delta", "bijsturen watt")

    @property
    def native_value(self) -> float:
        return _execution_plan_totals(self.coordinator)["delta_abs_w"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        totals = _execution_plan_totals(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_command_delta",
            **totals,
        }


class FlowCommandNeededSensor(BaseSensor):
    """Number of PowerStream groups that need a command to follow advice."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_command_needed", "bijsturen")

    @property
    def native_value(self) -> int:
        return int(_execution_plan_totals(self.coordinator)["command_needed_count"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        totals = _execution_plan_totals(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_command_needed",
            **totals,
        }


class FlowNextCommandSensor(BaseSensor):
    """Human-readable next PowerStream action for the simple dashboard flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_next_command", "volgende actie")

    @property
    def native_value(self) -> str:
        action = _next_dashboard_action(self.coordinator)
        return str(action.get("summary") or "stand-by")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        action = _next_dashboard_action(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_next_command",
            **action,
        }


class FlowActionStateSensor(BaseSensor):
    """Compact executability state for the simple dashboard flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_action_state", "uitvoerbaar")

    @property
    def native_value(self) -> str:
        action = _next_dashboard_action(self.coordinator)
        if action.get("action_type") == "error":
            return "fout"
        return scenario_execution_hint(action)

    @property
    def icon(self) -> str:
        return {
            "kan sturen": "mdi:check-circle",
            "testmodus": "mdi:flask",
            "data nodig": "mdi:database-alert",
            "scenario uit": "mdi:pause-circle",
            "wacht": "mdi:timer-sand",
            "fout": "mdi:alert-circle",
            "stand-by": "mdi:power-standby",
        }.get(self.native_value, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        action = _next_dashboard_action(self.coordinator)
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_action_state",
            "execution_hint": scenario_execution_hint(action),
            **action,
        }


class DashboardOverviewSensor(BaseSensor):
    """Compact overview of the configured and live system."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_overview", "overzicht")

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        settings = _dashboard_settings(self.coordinator)
        readiness = dashboard_readiness(data, settings)
        batteries = _configured_items(settings, "batteries")
        powerstreams = _configured_items(settings, "powerstreams")
        batteries_with_soc = _configured_batteries_with_soc(
            batteries, data.get("batteries") or {}
        )
        active_powerstreams = _configured_live_items(
            powerstreams, data.get("powerstreams") or {}
        )
        return (
            f"{readiness['status']}: "
            f"{batteries_with_soc}/{len(batteries)} accu SoC, "
            f"{active_powerstreams}/{len(powerstreams)} PS"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        settings = _dashboard_settings(self.coordinator)
        readiness = dashboard_readiness(data, settings)
        fleet = _battery_fleet_summary(self.coordinator)
        prices = data.get("prices") or []
        weather = data.get("weather") or {}
        batteries = _configured_items(settings, "batteries")
        powerstreams = _configured_items(settings, "powerstreams")
        homewizard_meters = _configured_items(settings, "homewizard_meters")
        batteries_with_soc = _configured_batteries_with_soc(
            batteries, data.get("batteries") or {}
        )
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_overview",
            "status": readiness["status"],
            "score": readiness["score"],
            "next_step": readiness["next_step"],
            "configured_batteries": len(batteries),
            "batteries_with_data": _configured_live_items(
                batteries,
                data.get("batteries") or {},
                require_values=True,
            ),
            "batteries_with_soc": batteries_with_soc,
            "batteries_missing_soc": max(0, len(batteries) - batteries_with_soc),
            "configured_powerstreams": len(powerstreams),
            "powerstreams_with_data": _configured_live_items(
                powerstreams,
                data.get("powerstreams") or {},
            ),
            "configured_homewizard_meters": len(homewizard_meters),
            "homewizard_meters_with_data": _configured_live_items(
                homewizard_meters,
                data.get("homewizard_meters") or {},
            ),
            "price_hours": len(prices),
            "weather_hours": len(weather.get("hourly") or []),
            "scenario_count": len(data.get("scenarios") or {}),
            "battery_soc": fleet.get("soc"),
            "available_kwh": fleet.get("available_kwh"),
            "price_now": data.get("price_now"),
            "corrected_solar_power": data.get("corrected_solar_power"),
            "test_mode": bool(settings.get("dry_run", True)),
        }


class DashboardEnergyFlowSensor(BaseSensor):
    """One-tile summary of input, output and battery state."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_energy_flow", "energiestroom")

    @property
    def native_value(self) -> str:
        flow = _energy_flow_summary(self.coordinator)
        return str(flow.get("summary"))

    @property
    def icon(self) -> str:
        return {
            "verbruik van net": "mdi:transmission-tower-import",
            "levering aan net": "mdi:transmission-tower-export",
            "accu laadt": "mdi:battery-arrow-up",
            "accu levert": "mdi:battery-arrow-down",
            "in balans": "mdi:scale-balance",
            "wacht op data": "mdi:progress-question",
        }.get(str(_energy_flow_summary(self.coordinator).get("state")), "mdi:home-lightning-bolt")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_energy_flow",
            **_energy_flow_summary(self.coordinator),
        }


class DashboardSetupSensor(BaseSensor):
    """Compact status showing whether the minimal local setup is complete."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_setup", "setup")

    @property
    def native_value(self) -> str:
        setup = _setup_state(self.coordinator)
        return str(setup.get("current_capability") or setup.get("state"))

    @property
    def icon(self) -> str:
        setup = _setup_state(self.coordinator)
        state = str(setup.get("state"))
        return {
            "compleet": "mdi:check-circle",
            "basis klaar": "mdi:lightbulb-on",
            "actie nodig": "mdi:alert-circle",
        }.get(state, "mdi:cog")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_setup",
            **_setup_state(self.coordinator),
        }


class DashboardSetupProgressSensor(BaseSensor):
    """Numeric progress for minimal setup completion."""

    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_setup_progress", "setup voortgang")

    @property
    def native_value(self) -> int:
        return int(_setup_state(self.coordinator).get("progress", 0))

    @property
    def icon(self) -> str:
        progress = self.native_value
        if progress >= 100:
            return "mdi:check-circle"
        if progress >= 60:
            return "mdi:progress-check"
        return "mdi:progress-alert"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_setup_progress",
            **_setup_state(self.coordinator),
        }


class DashboardSetupAdviceSensor(BaseSensor):
    """Readable setup advice for the one-dashboard flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_setup_advice", "setup advies")

    @property
    def native_value(self) -> str:
        return str(_setup_advice(self.coordinator).get("summary"))

    @property
    def icon(self) -> str:
        state = str(_setup_advice(self.coordinator).get("state"))
        return {
            "basis nodig": "mdi:cog-alert",
            "basis klaar": "mdi:lightbulb-on",
            "sturen klaar": "mdi:play-circle",
            "optimaal": "mdi:check-decagram",
        }.get(state, "mdi:cog")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_setup_advice",
            **_setup_advice(self.coordinator),
        }


class DashboardReadinessSensor(BaseSensor):
    """Simple dashboard data quality status."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_readiness", "dashboard gereed")

    @property
    def native_value(self) -> str:
        return dashboard_readiness(
            self.coordinator.data or {}, _dashboard_settings(self.coordinator)
        )["status"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        readiness = dashboard_readiness(
            self.coordinator.data or {}, _dashboard_settings(self.coordinator)
        )
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_readiness",
            **readiness,
        }


class DashboardSourceSummarySensor(BaseSensor):
    """Compact source summary for the simple dashboard flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_source_summary", "bronnen")

    @property
    def native_value(self) -> str:
        summary = source_summary(
            dashboard_readiness(
                self.coordinator.data or {}, _dashboard_settings(self.coordinator)
            )
        )
        return str(summary.get("summary"))

    @property
    def icon(self) -> str:
        status = str(
            source_summary(
                dashboard_readiness(
                    self.coordinator.data or {},
                    _dashboard_settings(self.coordinator),
                )
            ).get("status")
        )
        return {
            "klaar": "mdi:database-check",
            "gedeeltelijk": "mdi:database-clock",
            "actie nodig": "mdi:database-alert",
        }.get(status, "mdi:database-question")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        readiness = dashboard_readiness(
            self.coordinator.data or {}, _dashboard_settings(self.coordinator)
        )
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_source_summary",
            **source_summary(readiness),
        }


class DashboardProblemSensor(BaseSensor):
    """First problem or warning that needs attention in the main flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_problem", "aandacht")

    @property
    def native_value(self) -> str:
        problem = _dashboard_problem(self.coordinator)
        return str(problem.get("summary"))

    @property
    def icon(self) -> str:
        status = str(_dashboard_problem(self.coordinator).get("status"))
        return {
            "klaar": "mdi:check-circle",
            "gedeeltelijk": "mdi:alert-circle",
            "actie nodig": "mdi:close-circle",
        }.get(status, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_problem",
            **_dashboard_problem(self.coordinator),
        }


class DashboardLiveProofSensor(BaseSensor):
    """Compact proof that the main flow is backed by live data."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_live_proof", "live bewijs")

    @property
    def native_value(self) -> str:
        proof = _live_proof(self.coordinator)
        return (
            f"{proof['data_ready_sources']}/{proof['data_total_sources']} data, "
            f"sturing {proof['execution_status']}"
            if proof["total_sources"]
            else "geen bewijs"
        )

    @property
    def icon(self) -> str:
        status = _live_proof(self.coordinator)["status"]
        return {
            "klaar": "mdi:check-decagram",
            "gedeeltelijk": "mdi:progress-check",
            "actie nodig": "mdi:alert-decagram",
        }.get(str(status), "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_live_proof",
            **_live_proof(self.coordinator),
        }


class DashboardReadinessScoreSensor(BaseSensor):
    """Numeric dashboard readiness score."""

    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(
            coordinator, "dashboard_readiness_score", "dashboard score"
        )

    @property
    def native_value(self) -> float:
        return float(
            dashboard_readiness(
                self.coordinator.data or {}, _dashboard_settings(self.coordinator)
            )["score"]
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        readiness = dashboard_readiness(
            self.coordinator.data or {}, _dashboard_settings(self.coordinator)
        )
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_readiness_score",
            "status": readiness["status"],
            "ready": readiness["ready"],
            "blocking": readiness["blocking"],
            "warnings": readiness["warnings"],
        }


class DashboardInsightStateSensor(BaseSensor):
    """Visible status for minimal price and battery insight."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_insight_state", "basisinzicht")

    @property
    def native_value(self) -> str:
        return str(_simple_flow_stage(self.coordinator).get("state"))

    @property
    def icon(self) -> str:
        return {
            "basis nodig": "mdi:cog-alert",
            "data nodig": "mdi:database-alert",
            "inzicht klaar": "mdi:lightbulb-on",
            "sturing beperkt": "mdi:progress-wrench",
            "testmodus": "mdi:test-tube",
            "startbaar": "mdi:play-circle",
            "optimaliseren": "mdi:tune",
            "sturing klaar": "mdi:check-decagram",
            "actie nodig": "mdi:lightbulb-alert",
        }.get(self.native_value, "mdi:lightbulb-question")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        readiness = dashboard_readiness(
            self.coordinator.data or {}, _dashboard_settings(self.coordinator)
        )
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_insight_state",
            **_simple_flow_stage(self.coordinator),
            "insight_ready": readiness.get("insight_ready"),
            "insight_status": readiness.get("insight_status"),
            "insight_next_step": readiness.get("insight_next_step"),
            "insight_checks": readiness.get("insight_checks"),
            "control_ready": readiness.get("control_ready"),
            "dashboard_status": readiness.get("status"),
            "dashboard_score": readiness.get("score"),
            "basis": "basisinzicht vereist alleen prijsdata en batterij-SoC",
        }


class DashboardNextStepSensor(BaseSensor):
    """Most useful next action for the simple dashboard flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_next_step", "volgende stap")

    @property
    def native_value(self) -> str:
        return str(_dashboard_next_user_step(self.coordinator).get("summary"))

    @property
    def icon(self) -> str:
        state = str(_dashboard_next_user_step(self.coordinator).get("state"))
        return {
            "basis nodig": "mdi:cog-alert",
            "data nodig": "mdi:database-alert",
            "basis klaar": "mdi:lightbulb-on",
            "actie nodig": "mdi:alert-circle",
            "testmodus": "mdi:flask",
            "keuze aanpassen": "mdi:swap-horizontal",
            "startbaar": "mdi:play-circle",
            "wachten": "mdi:timer-sand",
            "optimaliseren": "mdi:tune",
            "klaar": "mdi:check-circle",
        }.get(state, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_next_step",
            **_dashboard_next_user_step(self.coordinator),
        }


class DashboardCheckSensor(BaseSensor):
    """Single readiness check surfaced as a dashboard entity."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, check_key: str, label: str
    ) -> None:
        super().__init__(
            coordinator, f"dashboard_check_{check_key}", f"check {label}"
        )
        self._check_key = check_key
        self._label = label

    @property
    def native_value(self) -> str:
        check = self._check()
        status = str(check.get("status", "onbekend"))
        message = str(check.get("message", "geen status"))
        return f"{status}: {message}"

    @property
    def icon(self) -> str:
        return {
            "klaar": "mdi:check-circle",
            "gedeeltelijk": "mdi:alert-circle",
            "actie nodig": "mdi:close-circle",
        }.get(str(self._check().get("status")), "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        check = self._check()
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_check",
            "check_key": self._check_key,
            "label": self._label,
            "status": check.get("status", "onbekend"),
            "message": check.get("message", "geen status"),
            "details": check.get("details", {}),
            **{
                f"detail_{key}": value
                for key, value in (check.get("details") or {}).items()
            },
        }

    def _check(self) -> dict[str, Any]:
        readiness = dashboard_readiness(
            self.coordinator.data or {}, _dashboard_settings(self.coordinator)
        )
        for check in readiness.get("checks", []):
            if check.get("key") == self._check_key:
                return check
        return {
            "key": self._check_key,
            "status": "onbekend",
            "message": "check ontbreekt",
        }


class CheapBandSensor(BaseSensor):
    """Automatic cheap price band sensor."""

    _attr_native_unit_of_measurement = "EUR/kWh"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "cheap_band", "goedkope prijsgrens")

    @property
    def native_value(self) -> float | None:
        return ((self.coordinator.data or {}).get("price_bands") or {}).get("cheap")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        bands = (self.coordinator.data or {}).get("price_bands") or {}
        return {
            "eec_device_type": "price",
            "eec_sensor_role": "price_cheap_band",
            "expensive": bands.get("expensive"),
            "basis": "automatisch uit komende prijsuren",
        }


class ExpensiveBandSensor(BaseSensor):
    """Automatic expensive price band sensor."""

    _attr_native_unit_of_measurement = "EUR/kWh"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "expensive_band", "dure prijsgrens")

    @property
    def native_value(self) -> float | None:
        return ((self.coordinator.data or {}).get("price_bands") or {}).get("expensive")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        bands = (self.coordinator.data or {}).get("price_bands") or {}
        return {
            "eec_device_type": "price",
            "eec_sensor_role": "price_expensive_band",
            "cheap": bands.get("cheap"),
            "basis": "automatisch uit komende prijsuren",
        }


class ScenarioActionSensor(BaseSensor):
    """Simulated scenario action."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, scenario_key: str, label: str
    ) -> None:
        super().__init__(coordinator, f"scenario_{scenario_key}_action", f"{label} actie")
        self._scenario_key = scenario_key

    @property
    def native_value(self) -> str:
        return _scenario_data(self.coordinator, self._scenario_key).get("action", "wachten")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _scenario_attrs(self.coordinator, self._scenario_key, "action")


class ScenarioPowerSensor(BaseSensor):
    """Simulated scenario power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, scenario_key: str, label: str
    ) -> None:
        super().__init__(coordinator, f"scenario_{scenario_key}_power", f"{label} vermogen")
        self._scenario_key = scenario_key

    @property
    def native_value(self) -> float:
        return float(_scenario_data(self.coordinator, self._scenario_key).get("power_w") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _scenario_attrs(self.coordinator, self._scenario_key, "power")


class ScenarioReasonSensor(BaseSensor):
    """Compact reason for a simulated scenario decision."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, scenario_key: str, label: str
    ) -> None:
        super().__init__(coordinator, f"scenario_{scenario_key}_reason", f"{label} reden")
        self._scenario_key = scenario_key

    @property
    def native_value(self) -> str:
        return _scenario_data(self.coordinator, self._scenario_key).get("reason", "wachten")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _scenario_attrs(self.coordinator, self._scenario_key, "reason")


class ScenarioExecutionSensor(BaseSensor):
    """Readable execution verdict for a simulated scenario."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, scenario_key: str, label: str
    ) -> None:
        super().__init__(
            coordinator, f"scenario_{scenario_key}_executable", f"{label} uitvoerbaar"
        )
        self._scenario_key = scenario_key

    @property
    def native_value(self) -> str:
        state = scenario_execution_state(
            _scenario_data(self.coordinator, self._scenario_key)
        )
        return str(state.get("state"))

    @property
    def icon(self) -> str:
        return {
            "uitvoerbaar": "mdi:play-circle",
            "data nodig": "mdi:database-alert",
            "wacht": "mdi:timer-sand",
        }.get(self.native_value, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        scenario = _scenario_data(self.coordinator, self._scenario_key)
        return {
            **_scenario_attrs(self.coordinator, self._scenario_key, "executable"),
            **scenario_execution_state(scenario),
        }


class ScenarioMoneyRateSensor(BaseSensor):
    """Simulated scenario live money rate."""

    _attr_native_unit_of_measurement = "EUR/h"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, scenario_key: str, label: str
    ) -> None:
        super().__init__(
            coordinator, f"scenario_{scenario_key}_eur_per_hour", f"{label} euro per uur"
        )
        self._scenario_key = scenario_key

    @property
    def native_value(self) -> float:
        return float(
            _scenario_data(self.coordinator, self._scenario_key).get("eur_per_hour") or 0
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _scenario_attrs(self.coordinator, self._scenario_key, "eur_per_hour")


class ScenarioTotalSensor(BaseSensor):
    """Simulated scenario cumulative money result."""

    _attr_native_unit_of_measurement = "EUR"

    def __init__(
        self,
        coordinator: EcoFlowEnergyCoordinator,
        scenario_key: str,
        label: str,
        period: str,
        period_label: str,
    ) -> None:
        super().__init__(
            coordinator,
            f"scenario_{scenario_key}_{period}_eur",
            f"{label} {period_label}",
        )
        self._scenario_key = scenario_key
        self._period = period

    @property
    def native_value(self) -> float:
        return float(
            _scenario_data(self.coordinator, self._scenario_key).get(
                f"{self._period}_eur", 0
            )
            or 0
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _scenario_attrs(
            self.coordinator, self._scenario_key, f"{self._period}_eur"
        )


class BatterySocSensor(BaseSensor):
    """Battery state of charge."""

    _attr_native_unit_of_measurement = "%"
    _attr_device_class = "battery"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_soc", "SoC")
        self._serial = serial
        _apply_device_entity_label(self, name, "SoC", "soc")
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> Any:
        return _battery_soc_value(_battery_values(self.coordinator, self._serial))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        values = _battery_values(self.coordinator, self._serial)
        return {
            **_device_attrs("battery", self._serial, "soc"),
            **_battery_soc_detail(values),
            "soc_candidates": _battery_soc_candidates(values),
        }


class BatteryAvailableEnergySensor(BaseSensor):
    """Available battery energy based on SoC and known/nominal capacity."""

    _attr_native_unit_of_measurement = "kWh"
    _attr_device_class = "energy"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_available_kwh", "beschikbaar")
        self._serial = serial
        self._name = name
        _apply_device_entity_label(self, name, "beschikbaar", "beschikbaar")
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> float:
        return _battery_available_kwh(
            _battery_values(self.coordinator, self._serial), self._name
        ) or 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        values = _battery_values(self.coordinator, self._serial)
        capacity = _battery_capacity_wh(values, self._name)
        soc = _battery_soc_value(values)
        return {
            **_device_attrs("battery", self._serial, "available_kwh"),
            "soc": soc,
            "capacity_wh": capacity,
            "available_wh": round(capacity * soc / 100, 0)
            if capacity is not None and soc is not None
            else None,
            "capacity_source": "telemetry_or_nominal",
            "energy_candidates": _battery_energy_candidates(values),
        }


class BatteryAvailableValueSensor(BaseSensor):
    """Current value of available battery energy at the live electricity price."""

    _attr_native_unit_of_measurement = "EUR"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_available_eur", "waarde")
        self._serial = serial
        self._name = name
        _apply_device_entity_label(self, name, "waarde", "waarde")
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> float:
        kwh = _battery_available_kwh(
            _battery_values(self.coordinator, self._serial), self._name
        )
        price = (self.coordinator.data or {}).get("price_now")
        if kwh is None or price is None:
            return 0.0
        return round(kwh * float(price), 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        kwh = _battery_available_kwh(
            _battery_values(self.coordinator, self._serial), self._name
        )
        return {
            **_device_attrs("battery", self._serial, "available_eur"),
            "available_kwh": kwh,
            "price_eur_kwh": (self.coordinator.data or {}).get("price_now"),
        }


class EcoFlowDeviceStatusSensor(BaseSensor):
    """Per-device EcoFlow API and telemetry status."""

    def __init__(
        self,
        coordinator: EcoFlowEnergyCoordinator,
        serial: str,
        name: str,
        device_type: str,
    ) -> None:
        super().__init__(coordinator, f"{serial}_api_status", "API status")
        self._serial = serial
        self._device_type = device_type
        _apply_device_entity_label(self, name, "API status", "api_status")
        self._attr_device_info = _ecoflow_device_info(serial, name, device_type)

    @property
    def native_value(self) -> str:
        item = self._device_data()
        if not item:
            return "wachten"
        if item.get("error"):
            return "fout"
        values = item.get("values") or {}
        if values:
            return "telemetrie ok"
        return "api ok, geen telemetrie"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = self._device_data()
        values = item.get("values", {}) if item else {}
        attrs = {
            "serial": self._serial,
            "device_type": self._device_type,
            "eec_device_type": self._device_type,
            "eec_sensor_role": "api_status",
            "api_connected": bool(item) and not item.get("error"),
            "telemetry_fields": len(values),
            "telemetry_keys": sorted(values.keys())[:40],
            "quota_source": item.get("quota_source") if item else None,
            "response_debug": item.get("response_debug") if item else None,
            "error": item.get("error") if item else None,
        }
        if self._device_type == "battery":
            attrs.update(
                {
                    "soc": _battery_soc_value(values),
                    **_battery_soc_detail(values),
                    "soc_candidates": _battery_soc_candidates(values),
                    "charge_w": _battery_charge_power(values),
                    "charge_source": _battery_charge_source(values),
                    "ac_charge_w": _battery_ac_charge_power(values),
                    "solar_charge_w": _battery_solar_charge_power(values),
                    "dc_charge_w": _battery_dc_charge_power(values),
                    "unclassified_input_w": _battery_unclassified_input_power(values),
                    "discharge_w": _battery_discharge_power(values),
                    "net_w": _battery_net_power(self.coordinator, self._serial),
                    "power_candidates": _battery_power_candidates(values),
                }
            )
        if self._device_type == "powerstream":
            attrs.update(
                {
                    "target_w": float(item.get("target_watts") or 0) if item else 0,
                    "raw_target_w": float(item.get("raw_target_watts") or 0) if item else 0,
                    "target_w_source": item.get("target_watts_source") if item else None,
                    "phase": item.get("phase") if item else None,
                    "managed_battery_serial": item.get("battery_serial") if item else None,
                    "managed_battery_name": item.get("battery_name") if item else None,
                    "managed_battery_soc": item.get("battery_soc") if item else None,
                    "power_candidates": _powerstream_power_candidates(values),
                }
            )
        if self._device_type == "smart_plug":
            attrs["charges"] = item.get("charges") if item else None
        return attrs

    def _device_data(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        group = {
            "battery": "batteries",
            "powerstream": "powerstreams",
            "smart_plug": "smart_plugs",
        }[self._device_type]
        return data.get(group, {}).get(self._serial, {})


class BatteryChargePowerSensor(BaseSensor):
    """Battery charge power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_charge_power", "laadvermogen")
        self._serial = serial
        _apply_device_entity_label(self, name, "laadvermogen", "laadvermogen")
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> float:
        return _battery_charge_power(_battery_values(self.coordinator, self._serial))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        values = _battery_values(self.coordinator, self._serial)
        return {
            **_device_attrs("battery", self._serial, "charge_power"),
            "charge_source": _battery_charge_source(values),
            "ac_charge_w": _battery_ac_charge_power(values),
            "solar_charge_w": _battery_solar_charge_power(values),
            "dc_charge_w": _battery_dc_charge_power(values),
            "unclassified_input_w": _battery_unclassified_input_power(values),
            "power_candidates": _battery_power_candidates(values),
        }


class BatteryDischargePowerSensor(BaseSensor):
    """Battery discharge power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_discharge_power", "ontlaadvermogen")
        self._serial = serial
        _apply_device_entity_label(self, name, "ontlaadvermogen", "ontlaadvermogen")
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> float:
        return _battery_discharge_power(_battery_values(self.coordinator, self._serial))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        values = _battery_values(self.coordinator, self._serial)
        return {
            **_device_attrs("battery", self._serial, "discharge_power"),
            "power_candidates": _battery_power_candidates(values),
        }


class BatteryChargeSourceSensor(BaseSensor):
    """Battery charge source."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_charge_source", "laadbron")
        self._serial = serial
        _apply_device_entity_label(self, name, "laadbron", "laadbron")
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> str:
        return _battery_charge_source(_battery_values(self.coordinator, self._serial))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        values = _battery_values(self.coordinator, self._serial)
        return {
            **_device_attrs("battery", self._serial, "charge_source"),
            "ac_charge_w": _battery_ac_charge_power(values),
            "solar_charge_w": _battery_solar_charge_power(values),
            "dc_charge_w": _battery_dc_charge_power(values),
            "unclassified_input_w": _battery_unclassified_input_power(values),
            "power_candidates": _battery_power_candidates(values),
        }


class BatteryNetPowerSensor(BaseSensor):
    """Battery net power: positive means discharging, negative means charging."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_net_power", "netto vermogen")
        self._serial = serial
        _apply_device_entity_label(self, name, "netto vermogen", "netto_vermogen")
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> float:
        return _battery_net_power(self.coordinator, self._serial)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        values = _battery_values(self.coordinator, self._serial)
        return {
            **_device_attrs("battery", self._serial, "net_power"),
            "power_candidates": _battery_power_candidates(values),
        }


class BatteryModeSensor(BaseSensor):
    """Battery direction."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_mode", "status")
        self._serial = serial
        _apply_device_entity_label(self, name, "status", "status")
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> str:
        net = _battery_net_power(self.coordinator, self._serial)
        return _battery_mode_from_net(net)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _device_attrs("battery", self._serial, "mode")


class PowerStreamTargetSensor(BaseSensor):
    """PowerStream target/export power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_powerstream_power", "vermogen")
        self._serial = serial
        _apply_device_entity_label(self, name, "vermogen", "vermogen")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> float:
        data = (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
        return float(data.get("target_watts") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
        values = _powerstream_values(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "power"),
            "telemetry_fields": len(values),
            "telemetry_keys": sorted(values.keys())[:40],
            "raw_target_w": data.get("raw_target_watts"),
            "target_w_source": data.get("target_watts_source"),
            "managed_battery_serial": data.get("battery_serial"),
            "managed_battery_name": data.get("battery_name"),
            "managed_battery_soc": data.get("battery_soc"),
            "phase": data.get("phase"),
            "power_candidates": _powerstream_power_candidates(values),
        }


class PowerStreamModeSensor(BaseSensor):
    """PowerStream status."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_powerstream_mode", "status")
        self._serial = serial
        _apply_device_entity_label(self, name, "status", "status")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> str:
        data = (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
        watts = float(data.get("target_watts") or 0)
        if watts > 20:
            return "terugleveren"
        if watts < -20:
            return "laden"
        return "stand-by"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
        values = _powerstream_values(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "mode"),
            "telemetry_fields": len(values),
            "telemetry_keys": sorted(values.keys())[:40],
            "raw_target_w": data.get("raw_target_watts"),
            "target_w_source": data.get("target_watts_source"),
            "managed_battery_serial": data.get("battery_serial"),
            "managed_battery_name": data.get("battery_name"),
            "managed_battery_soc": data.get("battery_soc"),
            "phase": data.get("phase"),
            "power_candidates": _powerstream_power_candidates(values),
        }


class PowerStreamGroupSuggestedPowerSensor(BaseSensor):
    """Suggested PowerStream output for this configured group."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_group_suggested_watts", "advies")
        self._serial = serial
        _apply_device_entity_label(self, name, "advies", "advies")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> float:
        item = _powerstream_plan_item(self.coordinator, self._serial)
        return float(item.get("suggested_watts") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = _powerstream_plan_item(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "group_suggested_watts"),
            **_powerstream_plan_attrs(item),
        }


class PowerStreamGroupDeltaPowerSensor(BaseSensor):
    """Wattage still needed for this group to follow the current advice."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_group_delta_watts", "nog")
        self._serial = serial
        _apply_device_entity_label(self, name, "nog", "nog")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> float:
        item = _powerstream_plan_item(self.coordinator, self._serial)
        return abs(float(item.get("delta_watts") or 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = _powerstream_plan_item(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "group_delta_watts"),
            **_powerstream_plan_attrs(item),
        }


class PowerStreamGroupCommandStatusSensor(BaseSensor):
    """Compact status showing whether this group needs a command."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_group_command_status", "bijsturen")
        self._serial = serial
        _apply_device_entity_label(self, name, "bijsturen", "bijsturen")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> str:
        item = _powerstream_plan_item(self.coordinator, self._serial)
        if item.get("strategy_error"):
            return "fout"
        if item.get("strategy_throttled"):
            return "wacht"
        if not item.get("current_watts_known") and not item.get("command_needed"):
            return "wacht"
        if item.get("current_watts_verified") is False and not item.get("command_needed"):
            return "wacht"
        if item.get("command_needed"):
            return "bijsturen"
        return "ok"

    @property
    def icon(self) -> str:
        return {
            "ok": "mdi:check-circle",
            "bijsturen": "mdi:tune",
            "wacht": "mdi:timer-sand",
            "fout": "mdi:alert-circle",
        }.get(self.native_value, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = _powerstream_plan_item(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "group_command_status"),
            **_powerstream_plan_attrs(item),
            "strategy_error": item.get("strategy_error"),
            "strategy_throttled": item.get("strategy_throttled"),
        }


class PowerStreamGroupBatterySocSensor(BaseSensor):
    """Battery SoC for the battery linked to a PowerStream."""

    _attr_native_unit_of_measurement = "%"
    _attr_device_class = "battery"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_group_battery_soc", "accu")
        self._serial = serial
        _apply_device_entity_label(self, name, "accu", "accu")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> float:
        value = _powerstream_data(self.coordinator, self._serial).get("battery_soc")
        return float(value) if value is not None else 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _powerstream_data(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "group_battery_soc"),
            "managed_battery_serial": data.get("battery_serial"),
            "managed_battery_name": data.get("battery_name"),
            "available_wh": _powerstream_group_available_wh(
                self.coordinator, self._serial
            ),
        }


class PowerStreamGroupAvailableEnergySensor(BaseSensor):
    """Available battery energy for the battery linked to a PowerStream."""

    _attr_native_unit_of_measurement = "Wh"
    _attr_device_class = "energy"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_group_available_wh", "beschikbaar")
        self._serial = serial
        _apply_device_entity_label(self, name, "beschikbaar", "beschikbaar")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> float:
        return _powerstream_group_available_wh(self.coordinator, self._serial) or 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _powerstream_data(self.coordinator, self._serial)
        battery_values = _linked_battery_values(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "group_available_wh"),
            "managed_battery_serial": data.get("battery_serial"),
            "managed_battery_name": data.get("battery_name"),
            "battery_soc": data.get("battery_soc"),
            "capacity_wh": _battery_capacity_wh(
                battery_values, data.get("battery_name")
            ),
            "energy_candidates": _battery_energy_candidates(battery_values),
        }


class PowerStreamGroupFreeEnergySensor(BaseSensor):
    """Free battery space for the battery linked to a PowerStream."""

    _attr_native_unit_of_measurement = "Wh"
    _attr_device_class = "energy"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_group_free_wh", "ruimte")
        self._serial = serial
        _apply_device_entity_label(self, name, "ruimte", "ruimte")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> float:
        return _powerstream_group_free_wh(self.coordinator, self._serial) or 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _powerstream_data(self.coordinator, self._serial)
        battery_values = _linked_battery_values(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "group_free_wh"),
            "managed_battery_serial": data.get("battery_serial"),
            "managed_battery_name": data.get("battery_name"),
            "battery_soc": data.get("battery_soc"),
            "capacity_wh": _battery_capacity_wh(
                battery_values, data.get("battery_name")
            ),
            "available_wh": _powerstream_group_available_wh(
                self.coordinator, self._serial
            ),
        }


class PowerStreamGroupActionSensor(BaseSensor):
    """Suggested group action based on strategy, price and corrected solar."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_group_action", "actie")
        self._serial = serial
        _apply_device_entity_label(self, name, "actie", "actie")
        self._attr_device_info = _ecoflow_device_info(serial, name, "powerstream")

    @property
    def native_value(self) -> str:
        return str(_powerstream_data(self.coordinator, self._serial).get("group_action") or "wachten")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _powerstream_data(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "group_action"),
            "strategy": data.get("group_strategy"),
            "suggested_watts": data.get("suggested_watts"),
            "decision_reason": data.get("decision_reason"),
            "can_charge": data.get("can_charge"),
            "can_discharge": data.get("can_discharge"),
            "charge_blocker": data.get("charge_blocker"),
            "discharge_blocker": data.get("discharge_blocker"),
            "strategy_throttled": data.get("strategy_throttled"),
            "strategy_next_update_seconds": data.get("strategy_next_update_seconds"),
            "strategy_error": data.get("strategy_error"),
            "command_source": data.get("command_source"),
            "managed_battery_name": data.get("battery_name"),
            "managed_battery_soc": data.get("battery_soc"),
            "managed_battery_free_wh": data.get("battery_free_wh"),
            "corrected_solar_power": (self.coordinator.data or {}).get(
                "corrected_solar_power"
            ),
            "price_now": (self.coordinator.data or {}).get("price_now"),
        }


class HomeWizardMeterStatusSensor(BaseSensor):
    """Per-meter HomeWizard local API status."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, host: str, name: str
    ) -> None:
        super().__init__(coordinator, f"homewizard_{host}_status", "status")
        self._host = host
        self._name = name
        _apply_device_entity_label(self, name, "status", "status")
        self._attr_device_info = _homewizard_device_info(host, name)

    @property
    def native_value(self) -> str:
        item = self._meter_data()
        if not item:
            return "wachten"
        if item.get("error") or item.get("available") is False:
            return "fout"
        return "api ok"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = self._meter_data()
        return {
            "eec_device_type": "homewizard",
            "eec_sensor_role": "api_status",
            "host": self._host,
            "role": item.get("role") if item else None,
            "error": item.get("error") if item else None,
            "wifi_ssid": item.get("wifi_ssid") if item else None,
            "wifi_strength": item.get("wifi_strength") if item else None,
            "meter_model": item.get("meter_model") if item else None,
        }

    def _meter_data(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("homewizard_meters", {})
        return data.get(self._name, {}) or data.get(self._host, {})


class HomeWizardMeterPowerSensor(BaseSensor):
    """Per-meter HomeWizard active power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, host: str, name: str
    ) -> None:
        super().__init__(coordinator, f"homewizard_{host}_power", "vermogen")
        self._host = host
        self._name = name
        _apply_device_entity_label(self, name, "vermogen", "vermogen")
        self._attr_device_info = _homewizard_device_info(host, name)

    @property
    def native_value(self) -> float:
        item = self._meter_data()
        return float(item.get("active_power_w") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = self._meter_data()
        return {
            "eec_device_type": "homewizard",
            "eec_sensor_role": "power",
            "host": self._host,
            "role": item.get("role") if item else None,
            "phase_power_w": item.get("phase_power_w", {}) if item else {},
            "phase_voltage_v": item.get("phase_voltage_v", {}) if item else {},
            "phase_current_a": item.get("phase_current_a", {}) if item else {},
        }

    def _meter_data(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("homewizard_meters", {})
        return data.get(self._name, {}) or data.get(self._host, {})


class HomeWizardMeterPhasePowerSensor(BaseSensor):
    """Per-phase HomeWizard active power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, host: str, name: str, phase: str
    ) -> None:
        super().__init__(
            coordinator,
            f"homewizard_{host}_{phase}_power",
            f"{phase.upper()} vermogen",
        )
        self._host = host
        self._name = name
        self._phase = phase
        _apply_device_entity_label(
            self, name, f"{phase.upper()} vermogen", f"{phase}_vermogen"
        )
        self._attr_device_info = _homewizard_device_info(host, name)

    @property
    def native_value(self) -> float | None:
        item = self._meter_data()
        value = (item.get("phase_power_w") or {}).get(self._phase)
        return float(value) if value is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = self._meter_data()
        return {
            "eec_device_type": "homewizard",
            "eec_sensor_role": "phase_power",
            "host": self._host,
            "phase": self._phase,
            "voltage_v": (item.get("phase_voltage_v") or {}).get(self._phase),
            "current_a": (item.get("phase_current_a") or {}).get(self._phase),
        }

    def _meter_data(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("homewizard_meters", {})
        return data.get(self._name, {}) or data.get(self._host, {})


class HomeWizardP1HistorySensor(BaseSensor):
    """P1 net import/export history from Home Assistant statistics."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = "energy"

    def __init__(
        self,
        coordinator: EcoFlowEnergyCoordinator,
        host: str,
        name: str,
        period: str,
        label: str,
    ) -> None:
        super().__init__(
            coordinator,
            f"homewizard_{host}_p1_net_{period}",
            f"P1 netto {label}",
        )
        self._host = host
        self._name = name
        self._period = period
        self._label = label
        _apply_device_entity_label(
            self, name, f"P1 netto {label}", f"p1_net_{period}"
        )
        self._attr_device_info = _homewizard_device_info(host, name)

    @property
    def native_value(self) -> float | None:
        return _as_float(self._period_data().get("net_import_kwh"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = self._meter_data()
        history = item.get("history") or {}
        period = self._period_data()
        return {
            "eec_device_type": "homewizard",
            "eec_sensor_role": "p1_history",
            "host": self._host,
            "period": self._period,
            "source": history.get("source"),
            "available": history.get("available"),
            "reason": history.get("reason"),
            "import_kwh": period.get("import_kwh"),
            "export_kwh": period.get("export_kwh"),
            "net_import_kwh": period.get("net_import_kwh"),
            "import_entities": history.get("import_entities", []),
            "export_entities": history.get("export_entities", []),
            "errors": history.get("errors", {}),
        }

    def _period_data(self) -> dict[str, Any]:
        history = self._meter_data().get("history") or {}
        return (history.get("periods") or {}).get(self._period, {})

    def _meter_data(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("homewizard_meters", {})
        return data.get(self._name, {}) or data.get(self._host, {})


class StatusSensor(BaseSensor):
    """Integration source status."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "status", "status")

    @property
    def native_value(self) -> str:
        return (self.coordinator.data or {}).get("status", "wachten op data")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "eec_device_type": "control",
            "eec_sensor_role": "app_status",
            "errors": data.get("errors", {}),
            "ecoflow_devices": data.get("ecoflow_devices", []),
            "last_powerstream_command": data.get("last_powerstream_command"),
            "last_powerstream_error": data.get("last_powerstream_error"),
        }


class ExecutionStatusSensor(BaseSensor):
    """Runtime execution state for strategy control."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "execution_status", "sturing status")

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        plan = _powerstream_execution_plan(self.coordinator)
        issues = _powerstream_issue_summary(plan)
        if data.get("last_powerstream_error"):
            return "fout"
        if issues["error_count"]:
            return "fout"
        if issues["throttled_count"]:
            return "wacht"
        if self.coordinator.dry_run:
            return "testmodus"
        powerstreams = _configured_items(
            _dashboard_settings(self.coordinator), "powerstreams"
        )
        if _configured_live_items(powerstreams, data.get("powerstreams") or {}):
            return "actief"
        return "wachten"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        plan = _powerstream_execution_plan(self.coordinator)
        issues = _powerstream_issue_summary(plan)
        throttled = [
            str(item.get("serial"))
            for item in plan
            if item.get("strategy_throttled")
        ]
        strategy_errors = {
            str(item.get("serial")): item.get("strategy_error")
            for item in plan
            if item.get("strategy_error")
        }
        return {
            "eec_device_type": "control",
            "eec_sensor_role": "execution_status",
            "dry_run": self.coordinator.dry_run,
            "last_action": data.get("last_action"),
            "last_powerstream_error": data.get("last_powerstream_error"),
            **issues,
            "strategy_errors": strategy_errors,
            "throttled_powerstreams": throttled,
            "powerstream_target_count": len(self.coordinator.powerstream_targets),
        }


class LastActionSensor(BaseSensor):
    """Last controller action."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "last_action", "laatste actie")

    @property
    def native_value(self) -> str | None:
        return (self.coordinator.data or {}).get("last_action")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "control",
            "eec_sensor_role": "last_action",
        }


def _battery_values(
    coordinator: EcoFlowEnergyCoordinator, serial: str
) -> dict[str, Any]:
    return (
        (coordinator.data or {})
        .get("batteries", {})
        .get(serial, {})
        .get("values", {})
    )


def _battery_soc_value(values: dict[str, Any]) -> float | None:
    for key in (
        "cmsBattSoc",
        "bmsBattSoc",
        "pd.soc",
        "ems.soc",
        "bms.soc",
        "bms_emsStatus.soc",
        "bms_bmsStatus.soc",
        "soc",
        "socLevel",
        "batteryLevel",
    ):
        value = values.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        return max(0.0, min(numeric, 100.0))
    for key, value in values.items():
        normalized = key.lower().replace("_", "").replace("-", "")
        if "soc" not in normalized and "batterylevel" not in normalized:
            continue
        if _is_soc_limit_or_setting(normalized):
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if 0 <= numeric <= 100:
            return numeric
    return None


def _battery_soc_detail(values: dict[str, Any]) -> dict[str, float | None]:
    return {
        "main_soc": _to_percentage(values.get("cmsBattSoc")),
        "extra_battery_soc": _to_percentage(values.get("bmsBattSoc")),
        "selected_soc": _battery_soc_value(values),
    }


def _battery_soc_candidates(values: dict[str, Any]) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    for key, value in values.items():
        normalized = key.lower().replace("_", "").replace("-", "")
        if "soc" in normalized or "batterylevel" in normalized:
            candidates[key] = value
    return dict(sorted(candidates.items())[:20])


def _battery_charge_power(values: dict[str, Any]) -> float:
    return round(
        _battery_ac_charge_power(values) + _battery_solar_charge_power(values), 1
    )


def _battery_charge_source(values: dict[str, Any]) -> str:
    ac = _battery_ac_charge_power(values)
    solar = _battery_solar_charge_power(values)
    dc = _battery_dc_charge_power(values)
    unclassified = _battery_unclassified_input_power(values)
    sources = []
    if ac > 0:
        sources.append("AC")
    if solar > 0:
        sources.append("zon")
    if sources:
        return " + ".join(sources)
    if dc > 0:
        return "DC/extra batterij"
    if unclassified > 0:
        return "onbekende input"
    return "geen"


def _battery_ac_charge_power(values: dict[str, Any]) -> float:
    return max(
        0.0,
        normalize_live_power_w(
            _first_value(
                values,
                (
                    "pd.acInWatts",
                    "inv.acInWatts",
                    "acInWatts",
                    "ac.inputWatts",
                    "acInPower",
                    "gridInputWatts",
                    "gridInputPower",
                ),
            )
        ),
    )


def _battery_solar_charge_power(values: dict[str, Any]) -> float:
    explicit = _first_value(
        values,
        (
            "pd.solarWatts",
            "mppt.inWatts",
            "mppt.inputWatts",
            "mppt.inputPower",
            "pv.inputWatts",
            "pv.inputPower",
            "solarInputWatts",
            "solarInputPower",
            "pvInPower",
            "pvInWatts",
        ),
    )
    if explicit:
        return max(0.0, normalize_live_power_w(explicit))
    return max(0.0, normalize_live_power_w(_classified_battery_power(values, "solar_charge")))


def _battery_dc_charge_power(values: dict[str, Any]) -> float:
    return max(
        0.0,
        normalize_live_power_w(
            _first_value(
                values,
                (
                    "pd.dcInWatts",
                    "dcInWatts",
                    "dcInPower",
                    "bms_emsStatus.inputWatts",
                    "bms_emsStatus.wattsInSum",
                    "bms_bmsStatus.inputWatts",
                    "bms_bmsStatus.wattsInSum",
                ),
            )
        ),
    )


def _battery_unclassified_input_power(values: dict[str, Any]) -> float:
    return max(
        0.0,
        normalize_live_power_w(
            _first_value(
                values,
                (
                    "pd.inputWatts",
                    "pd.wattsInSum",
                    "inv.inputWatts",
                    "inputWatts",
                    "wattsInSum",
                    "chargeWatts",
                    "chgWatts",
                    "chgPower",
                    "chargePower",
                    "bmsChgPower",
                    "cmsChgPower",
                    "bmsInputWatts",
                    "cmsInputWatts",
                    "powIn",
                    "powerIn",
                    "powInSumW",
                    "inputPower",
                ),
            )
        ),
    )


def _battery_discharge_power(values: dict[str, Any]) -> float:
    explicit = _first_value(
        values,
        (
            "pd.outputWatts",
            "pd.invOutWatts",
            "pd.wattsOutSum",
            "pd.acOutWatts",
            "pd.dcOutWatts",
            "bms_emsStatus.outputWatts",
            "bms_emsStatus.wattsOutSum",
            "bms_bmsStatus.outputWatts",
            "bms_bmsStatus.wattsOutSum",
            "inv.acOutWatts",
            "inv.outputWatts",
            "outputWatts",
            "wattsOutSum",
            "dischargeWatts",
            "dsgWatts",
            "dsgPower",
            "dischargePower",
            "bmsDsgPower",
            "cmsDsgPower",
            "acOutPower",
            "dcOutPower",
            "bmsOutputWatts",
            "cmsOutputWatts",
            "powOut",
            "powerOut",
            "powOutSumW",
            "outputPower",
        ),
    )
    if explicit:
        return max(0.0, normalize_live_power_w(explicit))
    return max(0.0, normalize_live_power_w(_classified_battery_power(values, "discharge")))


def _classified_battery_power(values: dict[str, Any], direction: str) -> float:
    for key, value in values.items():
        normalized = _normalize_key(key)
        if not _looks_like_live_power_key(normalized):
            continue
        numeric = _to_float(value)
        if numeric is None:
            continue
        if direction == "solar_charge" and any(
            part in normalized
            for part in ("solar", "pv", "mppt")
        ):
            return numeric
        if direction == "charge" and any(
            part in normalized
            for part in (
                "input",
                "charge",
                "chg",
                "powin",
                "powerin",
                "wattsin",
                "insum",
                "acin",
                "dcin",
                "pvin",
            )
        ):
            return numeric
        if direction == "discharge" and any(
            part in normalized
            for part in (
                "output",
                "discharge",
                "dsg",
                "powout",
                "powerout",
                "wattsout",
                "outsum",
                "acout",
                "dcout",
                "invout",
            )
        ):
            return numeric
    return 0.0


def _battery_power_candidates(values: dict[str, Any]) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    for key, value in values.items():
        normalized = _normalize_key(key)
        if _looks_like_power_key(normalized):
            candidates[key] = value
    return dict(sorted(candidates.items())[:30])


def _to_percentage(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(numeric, 100.0)), 2)


def _is_soc_limit_or_setting(normalized_key: str) -> bool:
    return any(
        part in normalized_key
        for part in (
            "min",
            "max",
            "backup",
            "reserve",
            "generator",
            "oil",
            "alwayson",
            "conflict",
            "limit",
            "start",
            "stop",
        )
    )


def _scenario_data(
    coordinator: EcoFlowEnergyCoordinator, scenario_key: str
) -> dict[str, Any]:
    return (coordinator.data or {}).get("scenarios", {}).get(scenario_key, {})


def _scenario_attrs(
    coordinator: EcoFlowEnergyCoordinator, scenario_key: str, sensor_role: str
) -> dict[str, Any]:
    data = _scenario_data(coordinator, scenario_key)
    coordinator_data = coordinator.data or {}
    bands = coordinator_data.get("price_bands") or {}
    return {
        "eec_device_type": "scenario",
        "eec_scenario": scenario_key,
        "eec_sensor_role": f"scenario_{sensor_role}",
        "label": data.get("label", SCENARIOS.get(scenario_key, scenario_key)),
        "action": data.get("action"),
        "reason": data.get("reason"),
        "power_w": data.get("power_w"),
        "eur_per_hour": data.get("eur_per_hour"),
        "day_eur": data.get("day_eur"),
        "week_eur": data.get("week_eur"),
        "month_eur": data.get("month_eur"),
        "battery_soc": data.get("battery_soc"),
        "input_ready": data.get("input_ready"),
        "input_warnings": data.get("input_warnings"),
        "price_eur_kwh": data.get("price_eur_kwh"),
        "price_cheap_band": bands.get("cheap"),
        "price_expensive_band": bands.get("expensive"),
        "corrected_solar_power": coordinator_data.get("corrected_solar_power"),
    }


def _best_scenario(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    return best_scenario((coordinator.data or {}).get("scenarios", {}), SCENARIOS)


def _scenario_choice_summary(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    selected_key = _selected_scenario_key(coordinator.strategy)
    best = _best_scenario(coordinator)
    selected_data = _scenario_data(coordinator, selected_key) if selected_key else {}
    return scenario_choice_summary(
        coordinator.strategy,
        selected_key,
        selected_data,
        best,
    )


def _scenario_overview(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    best = _best_scenario(coordinator)
    choice = _scenario_choice_summary(coordinator)
    selected_key = _selected_scenario_key(coordinator.strategy)
    selected = _scenario_data(coordinator, selected_key) if selected_key else {}
    action_state = _next_dashboard_action(coordinator)
    executable = scenario_execution_state(best)
    label = best.get("label") or "wachten"
    action = best.get("action") or "wachten"
    power = _as_float(best.get("power_w")) or 0
    eur_per_hour = _as_float(best.get("eur_per_hour")) or 0
    day = _as_float(best.get("day_eur")) or 0
    best_plan = _scenario_plan_summary(label, best)
    selected_plan = (
        _scenario_plan_summary(str(selected.get("label") or "Uit"), selected)
        if selected_key
        else "Uit: geen automatische sturing"
    )
    if selected_key is None:
        state = "uit"
        summary = f"uit; advies {label}: {action}"
    elif not best.get("key"):
        state = "data nodig"
        summary = "wacht op scenario-data"
    elif executable.get("actionable") is False and best.get("input_ready") is False:
        state = "data nodig"
        summary = str(executable.get("summary") or "data nodig")
    elif choice.get("state") == "wijkt af":
        state = "wijkt af"
        summary = (
            f"{choice.get('selected_label')}: {selected.get('action') or 'wachten'}; "
            f"advies {label}: {action} ({eur_per_hour:+.2f} EUR/u)"
        )
    elif executable.get("actionable"):
        state = "volgt advies" if selected_key == best.get("key") else "wacht"
        summary = f"{label}: {action} {power:.0f} W, {eur_per_hour:+.2f} EUR/u"
    else:
        state = "wacht"
        summary = f"{label}: {action}; {best.get('reason') or 'geen actie'}"
    return {
        "state": state,
        "summary": summary,
        "best_scenario_key": best.get("key"),
        "best_label": label,
        "best_action": action,
        "best_reason": best.get("reason"),
        "best_power_w": best.get("power_w"),
        "best_eur_per_hour": best.get("eur_per_hour"),
        "best_day_eur": best.get("day_eur"),
        "best_week_eur": best.get("week_eur"),
        "best_month_eur": best.get("month_eur"),
        "best_actionable": scenario_is_actionable(best),
        "execution_state": executable.get("state"),
        "execution_summary": executable.get("summary"),
        "execution_blocker": executable.get("blocker"),
        "selected_strategy": coordinator.strategy,
        "selected_scenario_key": selected_key,
        "selected_label": selected.get("label") if selected_key else "Uit",
        "selected_action": selected.get("action"),
        "selected_reason": selected.get("reason"),
        "selected_eur_per_hour": selected.get("eur_per_hour"),
        "selected_plan": selected_plan,
        "choice_state": choice.get("state"),
        "choice_summary": choice.get("summary"),
        "delta_eur_per_hour": choice.get("delta_eur_per_hour"),
        "best_plan": best_plan,
        "plan_summary": selected_plan if choice.get("state") == "wijkt af" else best_plan,
        "next_command": action_state.get("summary"),
        "can_execute": action_state.get("can_execute"),
        "command_required": action_state.get("command_required"),
        "blocked_by": action_state.get("blocked_by"),
        "execution_hint": scenario_execution_hint(action_state),
        "test_mode": coordinator.dry_run,
        "price_now": (coordinator.data or {}).get("price_now"),
        "corrected_solar_power": (coordinator.data or {}).get("corrected_solar_power"),
        "basis": "beste scenario, gekozen scenario en uitvoerbaarheid in een regel",
        "day_eur_label": f"{day:+.2f} EUR vandaag",
    }


def _scenario_plan_summary(label: str, scenario: dict[str, Any]) -> str:
    action = scenario.get("action") or "wachten"
    reason = scenario.get("reason") or "geen reden"
    power = _as_float(scenario.get("power_w")) or 0
    eur_per_hour = _as_float(scenario.get("eur_per_hour")) or 0
    if abs(power) >= 1:
        return f"{label}: {action} {power:.0f} W; {reason}; {eur_per_hour:+.2f} EUR/u"
    return f"{label}: {action}; {reason}; {eur_per_hour:+.2f} EUR/u"


def _state_text(value: Any, limit: int = 250) -> str:
    text = str(value or "wachten")
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 3)]}..."


def _selected_scenario_key(strategy: str) -> str | None:
    return {
        STRATEGY_SELF_USE: "self_use",
        STRATEGY_EXPORT: "trading",
        STRATEGY_BUFFER_50: "buffer_50",
        STRATEGY_IDLE: None,
    }.get(strategy)


def _battery_fleet_summary(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    total_capacity_wh = 0.0
    total_available_wh = 0.0
    total_charge_w = 0.0
    total_discharge_w = 0.0
    total_net_w = 0.0
    batteries = []
    configured = {
        str(device.get("serial")): str(device.get("name") or device.get("serial"))
        for device in coordinator.settings.get("batteries", [])
        if device.get("serial")
    }
    data_batteries = (coordinator.data or {}).get("batteries") or {}
    for serial, name in configured.items():
        item = data_batteries.get(serial, {})
        values = item.get("values", {}) if isinstance(item, dict) else {}
        soc = _battery_soc_value(values)
        capacity = _battery_capacity_wh(values, name)
        charge_w = _battery_charge_power(values)
        discharge_w = _battery_discharge_power(values)
        net_w = _battery_net_power(coordinator, serial)
        total_charge_w += charge_w
        total_discharge_w += discharge_w
        total_net_w += net_w
        if soc is None or capacity is None:
            batteries.append(
                {
                    "serial": serial,
                    "name": name,
                    "soc": soc,
                    "capacity_kwh": round(capacity / 1000, 2) if capacity else None,
                    "available_kwh": None,
                    "free_kwh": None,
                    "charge_w": round(charge_w, 0),
                    "discharge_w": round(discharge_w, 0),
                    "net_w": round(net_w, 0),
                    "mode": _battery_mode_from_net(net_w),
                }
            )
            continue
        available = capacity * float(soc) / 100
        free = max(0.0, capacity - available)
        total_capacity_wh += capacity
        total_available_wh += available
        batteries.append(
            {
                "serial": serial,
                "name": name,
                "soc": round(float(soc), 1),
                "capacity_kwh": round(capacity / 1000, 2),
                "available_kwh": round(available / 1000, 2),
                "free_kwh": round(free / 1000, 2),
                "charge_w": round(charge_w, 0),
                "discharge_w": round(discharge_w, 0),
                "net_w": round(net_w, 0),
                "mode": _battery_mode_from_net(net_w),
            }
        )
    free_wh = max(0.0, total_capacity_wh - total_available_wh)
    return {
        "soc": round(total_available_wh / total_capacity_wh * 100, 1)
        if total_capacity_wh
        else 0.0,
        "available_kwh": round(total_available_wh / 1000, 2),
        "free_kwh": round(free_wh / 1000, 2),
        "capacity_kwh": round(total_capacity_wh / 1000, 2),
        "charge_w": round(total_charge_w, 0),
        "discharge_w": round(total_discharge_w, 0),
        "net_w": round(total_net_w, 0),
        "battery_count": len(batteries),
        "batteries": batteries,
    }


def _battery_mode_from_net(net: float) -> str:
    if net > 20:
        return "ontladen"
    if net < -20:
        return "laden"
    return "stand-by"


def _energy_flow_summary(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    data = coordinator.data or {}
    fleet = _battery_fleet_summary(coordinator)
    grid_power = _to_float(data.get("corrected_grid_power"))
    solar_power = _to_float(data.get("corrected_solar_power"))
    powerstream_export = _to_float(data.get("powerstream_export_w")) or 0.0
    battery_net = _to_float(fleet.get("net_w")) or 0.0
    battery_soc = fleet.get("soc")
    if grid_power is None and solar_power is None and not fleet.get("battery_count"):
        state = "wacht op data"
    elif grid_power is not None and grid_power > 20:
        state = "verbruik van net"
    elif grid_power is not None and grid_power < -20:
        state = "levering aan net"
    elif battery_net < -20:
        state = "accu laadt"
    elif battery_net > 20:
        state = "accu levert"
    else:
        state = "in balans"
    grid_label = _grid_flow_label(grid_power)
    summary = (
        f"{grid_label}, accu {round(float(battery_soc or 0), 0):.0f}%, "
        f"PS {_format_w(powerstream_export)}"
    )
    return {
        "state": state,
        "summary": summary,
        "grid_label": grid_label,
        "grid_power_w": grid_power,
        "solar_net_w": solar_power,
        "powerstream_export_w": powerstream_export,
        "battery_soc": battery_soc,
        "battery_available_kwh": fleet.get("available_kwh"),
        "battery_free_kwh": fleet.get("free_kwh"),
        "battery_charge_w": fleet.get("charge_w"),
        "battery_discharge_w": fleet.get("discharge_w"),
        "battery_net_w": battery_net,
        "battery_count": fleet.get("battery_count"),
        "price_now": data.get("price_now"),
        "strategy": coordinator.strategy,
        "test_mode": coordinator.dry_run,
        "meaning": "positieve netwaarde is verbruik van net; negatieve netwaarde is levering aan net",
        "batteries": fleet.get("batteries"),
    }


def _grid_flow_label(grid_power: float | None) -> str:
    if grid_power is None:
        return "net onbekend"
    if grid_power > 20:
        return f"net {_format_w(grid_power)} verbruik"
    if grid_power < -20:
        return f"net {_format_w(abs(grid_power))} levering"
    return "net neutraal"


def _format_w(value: float | int | None) -> str:
    return f"{round(float(value or 0), 0):.0f} W"


def _homewizard_grid_status(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    settings = _dashboard_settings(coordinator)
    grid_sources = [
        item
        for item in settings.get("homewizard_meters", [])
        if item.get("role") == HOMEWIZARD_ROLE_GRID_METER
    ]
    data = coordinator.data or {}
    grid_power = data.get("corrected_grid_power")
    if not grid_sources:
        state = "P1 ontbreekt"
        message = "HomeWizard P1/netmeter niet ingesteld"
    elif grid_power is None:
        state = "P1 wacht"
        message = "wacht op P1/netmeter data"
    else:
        state = "P1 ok"
        message = "P1/netmeter data beschikbaar"
    return {
        "state": state,
        "message": message,
        "configured_grid_meters": len(grid_sources),
        "grid_power_w": data.get("homewizard_grid_power"),
        "corrected_grid_power_w": grid_power,
        "corrected_grid_phase_power": data.get("corrected_grid_phase_power"),
        "meaning": "positief is verbruik van net; negatief is levering aan net",
    }


def _fleet_attrs(sensor_role: str) -> dict[str, Any]:
    return {
        "eec_device_type": "battery_fleet",
        "eec_sensor_role": sensor_role,
    }


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _price_context_label(data: dict[str, Any]) -> str:
    price = _as_float(data.get("price_now"))
    bands = data.get("price_bands") or {}
    cheap = _as_float(bands.get("cheap"))
    expensive = _as_float(bands.get("expensive"))
    if price is None:
        return "prijs onbekend"
    if cheap is not None and price <= cheap:
        return "goedkoop"
    if expensive is not None and price >= expensive:
        return "duur"
    return "normale prijs"


def _solar_context_label(value: Any) -> str:
    solar = _as_float(value)
    if solar is None:
        return "zon onbekend"
    if solar >= 500:
        return "veel zon"
    if solar >= 100:
        return "zon"
    if solar <= -100:
        return "netto verbruik"
    return "weinig zon"


def _dashboard_settings(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    settings = dict(coordinator.settings)
    settings["dry_run"] = coordinator.dry_run
    return settings


def _flow_start_state(
    readiness: dict[str, Any], actionable: bool, dry_run: bool
) -> str:
    if readiness.get("status") != "klaar":
        return "actie nodig"
    if not actionable:
        return "wachten"
    if dry_run:
        return "testmodus"
    return "startbaar"


def _flow_start_reason(
    readiness: dict[str, Any], best: dict[str, Any], start_state: str
) -> str:
    if start_state == "actie nodig":
        return str(readiness.get("next_step") or "controleer datacheck")
    if start_state == "wachten":
        return str(best.get("reason") or "geen actie nodig")
    if start_state == "testmodus":
        return "testmodus simuleert sturing"
    return str(best.get("reason") or "advies kan worden gestart")


def _start_context(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    data = coordinator.data or {}
    readiness = dashboard_readiness(data, _dashboard_settings(coordinator))
    best = _best_scenario(coordinator)
    actionable = scenario_is_actionable(best)
    state = _flow_start_state(readiness, actionable, coordinator.dry_run)
    return {
        "state": state,
        "reason": _flow_start_reason(readiness, best, state),
        "best_actionable": actionable,
        "best_scenario_key": best.get("key"),
        "best_label": best.get("label"),
        "best_action": best.get("action"),
        "best_reason": best.get("reason"),
        "readiness_status": readiness.get("status"),
        "readiness_score": readiness.get("score"),
        "test_mode": coordinator.dry_run,
    }


def _auto_mode_state(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    data = coordinator.data or {}
    readiness = dashboard_readiness(data, _dashboard_settings(coordinator))
    best = _best_scenario(coordinator)
    actionable = scenario_is_actionable(best)
    selected_key = _selected_scenario_key(coordinator.strategy)
    dry_run = coordinator.dry_run

    if readiness.get("status") == "actie nodig":
        state = "geblokkeerd"
        reason = readiness.get("next_step")
    elif dry_run:
        state = "testmodus"
        reason = "testmodus simuleert automatische sturing"
    elif not actionable:
        state = "wachten"
        reason = best.get("reason") or "geen uitvoerbaar advies"
    elif selected_key is None:
        state = "uit"
        reason = "scenario staat uit"
    elif selected_key == best.get("key"):
        state = "actief"
        reason = best.get("reason") or "volgt beste advies"
    else:
        state = "wijkt af"
        reason = "gekozen scenario wijkt af van beste advies"

    return {
        "state": state,
        "reason": reason,
        "readiness_status": readiness.get("status"),
        "readiness_score": readiness.get("score"),
        "next_step": readiness.get("next_step"),
        "selected_strategy": coordinator.strategy,
        "selected_scenario_key": selected_key,
        "best_scenario_key": best.get("key"),
        "best_label": best.get("label"),
        "best_action": best.get("action"),
        "best_actionable": actionable,
        "dry_run": dry_run,
    }


def _control_verdict(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    auto_mode = _auto_mode_state(coordinator)
    start = _start_context(coordinator)
    ready = _flow_ready_state(coordinator)
    action = _next_dashboard_action(coordinator)
    choice = _scenario_choice_summary(coordinator)
    confidence = _scenario_confidence(coordinator)
    guard = _powerstream_issue_summary(_powerstream_execution_plan(coordinator))
    command = str(action.get("summary") or "stand-by")
    state = str(auto_mode.get("state") or ready.get("state") or "wachten")
    reason = str(auto_mode.get("reason") or ready.get("reason") or command)
    if action.get("can_execute"):
        summary = f"mag sturen: {command}"
        state = "mag sturen"
    elif coordinator.dry_run:
        summary = f"testmodus: {command}"
        state = "testmodus"
    elif auto_mode.get("state") == "geblokkeerd":
        summary = f"blokkeert: {reason}"
        state = "blokkeert"
    elif auto_mode.get("state") == "uit":
        summary = "uit: automatische sturing staat stil"
        state = "uit"
    elif choice.get("state") == "wijkt af":
        summary = str(choice.get("summary") or "gekozen scenario wijkt af")
        state = "wijkt af"
    else:
        summary = f"wacht: {command}"
        state = "wacht"
    return {
        "state": state,
        "summary": summary,
        "reason": reason,
        "icon": {
            "mag sturen": "mdi:check-circle",
            "testmodus": "mdi:flask",
            "blokkeert": "mdi:alert-circle",
            "uit": "mdi:pause-circle",
            "wijkt af": "mdi:swap-horizontal",
            "wacht": "mdi:timer-sand",
        }.get(state, "mdi:help-circle"),
        "can_execute": action.get("can_execute"),
        "command_required": action.get("command_required"),
        "next_command": command,
        "blocked_by": action.get("blocked_by"),
        "readiness_status": auto_mode.get("readiness_status"),
        "readiness_score": auto_mode.get("readiness_score"),
        "test_mode": coordinator.dry_run,
        "selected_strategy": coordinator.strategy,
        "choice_state": choice.get("state"),
        "choice_summary": choice.get("summary"),
        "start_state": start.get("state"),
        "start_reason": start.get("reason"),
        "confidence_score": confidence.get("score"),
        "confidence_state": confidence.get("state"),
        "command_guard": _command_guard_summary(guard),
        "command_min_interval_seconds": POWERSTREAM_STRATEGY_MIN_INTERVAL_SECONDS,
        "command_error_count": guard.get("error_count"),
        "command_first_error_name": guard.get("first_error_name"),
        "command_first_error_message": guard.get("first_error_message"),
        "command_throttled_count": guard.get("throttled_count"),
        "command_first_throttled_name": guard.get("first_throttled_name"),
        "command_first_throttled_seconds": guard.get("first_throttled_seconds"),
        "best_scenario_key": auto_mode.get("best_scenario_key"),
        "best_label": auto_mode.get("best_label"),
        "best_action": auto_mode.get("best_action"),
        "best_actionable": auto_mode.get("best_actionable"),
    }


def _main_summary(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    step = _dashboard_next_user_step(coordinator)
    snapshot = _flow_snapshot(coordinator)
    live = _live_validation(coordinator)
    action = _next_dashboard_action(coordinator)
    fleet = _battery_fleet_summary(coordinator)
    setup = _setup_state(coordinator)
    data = coordinator.data or {}
    battery_soc = _as_float(fleet.get("soc"))
    available_kwh = _as_float(fleet.get("available_kwh"))
    charge_w = _as_float(fleet.get("charge_w")) or 0
    discharge_w = _as_float(fleet.get("discharge_w")) or 0
    export_w = _as_float(data.get("powerstream_export_w")) or 0
    corrected_solar = _as_float(data.get("corrected_solar_power")) or 0
    price_now = _as_float(data.get("price_now"))
    battery_label = (
        f"{battery_soc:.0f}% / {available_kwh:.1f} kWh"
        if battery_soc is not None and available_kwh is not None
        else "accu onbekend"
    )
    energy_line = (
        f"accu {battery_label}; in {charge_w:.0f} W; uit {discharge_w:.0f} W; "
        f"terug {export_w:.0f} W; netto zon {corrected_solar:.0f} W"
    )
    price_line = (
        f"{price_now:.3f} EUR/kWh"
        if price_now is not None
        else str(snapshot.get("price_context") or "prijs onbekend")
    )
    scenario_line = str(
        action.get("summary") or snapshot.get("best_action") or "wachten"
    )
    proof_line = str(
        live.get("summary") or snapshot.get("source_summary") or "geen bewijs"
    )
    state = str(step.get("state") or live.get("state") or snapshot.get("snapshot_state"))
    return {
        "state": state,
        "summary": f"{state}: {step.get('summary') or proof_line}",
        "icon": str(snapshot.get("snapshot_icon") or "mdi:view-dashboard"),
        "step": step.get("summary"),
        "step_state": step.get("state"),
        "energy": energy_line,
        "battery": battery_label,
        "battery_soc": battery_soc,
        "available_kwh": available_kwh,
        "charge_w": charge_w,
        "discharge_w": discharge_w,
        "powerstream_export_w": export_w,
        "corrected_solar_power": corrected_solar,
        "price": price_line,
        "price_now": price_now,
        "setup_price_source": setup.get("price_source"),
        "setup_price_source_defaulted": setup.get("price_source_defaulted"),
        "setup_price_note": (
            "EnergyZero standaard"
            if setup.get("price_source_defaulted")
            else str(setup.get("price_source") or "prijsbron ingesteld")
        ),
        "scenario": scenario_line,
        "best_label": snapshot.get("best_label"),
        "best_action": snapshot.get("best_action"),
        "best_eur_per_hour": snapshot.get("best_eur_per_hour"),
        "proof": proof_line,
        "live_state": live.get("state"),
        "readiness_status": snapshot.get("readiness_status"),
        "readiness_score": snapshot.get("readiness_score"),
        "control_ready": snapshot.get("control_ready"),
        "can_execute": action.get("can_execute"),
        "test_mode": coordinator.dry_run,
        "basis": "status, stap, energie, scenario en bewijs in een compacte hoofdregel",
    }


def _flow_ready_state(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    data = coordinator.data or {}
    readiness = dashboard_readiness(data, _dashboard_settings(coordinator))
    best = _best_scenario(coordinator)
    choice = _scenario_choice_summary(coordinator)
    next_action = _next_dashboard_action(coordinator)
    verdict = flow_ready_state(
        readiness,
        best,
        choice,
        next_action,
        coordinator.dry_run,
        coordinator.strategy,
    )

    return {
        **verdict,
        "readiness_status": readiness.get("status"),
        "readiness_score": readiness.get("score"),
        "next_step": readiness.get("next_step"),
        "test_mode": coordinator.dry_run,
        "selected_strategy": coordinator.strategy,
        "choice_state": choice.get("state"),
        "choice_summary": choice.get("summary"),
        "best_scenario_key": best.get("key"),
        "best_label": best.get("label"),
        "best_action": best.get("action"),
        "next_action": next_action.get("summary"),
        "can_execute": next_action.get("can_execute"),
        "command_required": next_action.get("command_required"),
        "blocked_by": next_action.get("blocked_by"),
    }


def _flow_snapshot(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    data = coordinator.data or {}
    readiness = dashboard_readiness(data, _dashboard_settings(coordinator))
    sources = source_summary(readiness)
    best = _best_scenario(coordinator)
    fleet = _battery_fleet_summary(coordinator)
    plan = _powerstream_execution_plan(coordinator)
    totals = _execution_plan_totals(coordinator)
    next_action = _next_dashboard_action(coordinator)
    snapshot_state = flow_snapshot_state(readiness, next_action, coordinator.dry_run)
    snapshot_icon = flow_snapshot_icon(snapshot_state)
    flow_phase = flow_snapshot_phase(snapshot_state)
    price_context = _price_context_label(data)
    solar_context = _solar_context_label(data.get("corrected_solar_power"))
    best_label = best.get("label") or "wachten"
    best_action = best.get("action") or "wachten"
    available = _as_float(fleet.get("available_kwh")) or 0
    delta = _as_float(totals.get("delta_abs_w")) or 0
    if readiness.get("status") == "actie nodig":
        summary = f"actie nodig: {sources.get('summary') or readiness.get('next_step')}"
    elif readiness.get("control_ready"):
        summary = (
            f"sturing klaar: {best_label}: {best_action}; {available:.1f} kWh; "
            f"{price_context}; {solar_context}; nog {delta:.0f} W"
        )
    elif readiness.get("insight_ready"):
        source_hint = sources.get("summary") or readiness.get("next_step")
        summary = (
            f"basis klaar: {best_label}: {best_action}; {available:.1f} kWh; "
            f"{price_context}; aandacht: {source_hint}"
        )
    else:
        summary = (
            f"{best_label}: {best_action}; {available:.1f} kWh; "
            f"{price_context}; {solar_context}; nog {delta:.0f} W"
        )
    return {
        "summary": summary,
        "readiness_status": readiness.get("status"),
        "readiness_score": readiness.get("score"),
        "insight_ready": readiness.get("insight_ready"),
        "insight_status": readiness.get("insight_status"),
        "insight_next_step": readiness.get("insight_next_step"),
        "control_ready": readiness.get("control_ready"),
        "next_step": readiness.get("next_step"),
        "source_summary": sources.get("summary"),
        "first_issue_key": sources.get("first_issue_key"),
        "first_issue_label": sources.get("first_issue_label"),
        "first_issue_status": sources.get("first_issue_status"),
        "first_issue_message": sources.get("first_issue_message"),
        "price_context": price_context,
        "solar_context": solar_context,
        "price_now": data.get("price_now"),
        "corrected_solar_power": data.get("corrected_solar_power"),
        "battery_soc": fleet.get("soc"),
        "available_kwh": fleet.get("available_kwh"),
        "free_kwh": fleet.get("free_kwh"),
        "best_scenario_key": best.get("key"),
        "best_label": best_label,
        "best_action": best_action,
        "best_reason": best.get("reason"),
        "best_eur_per_hour": best.get("eur_per_hour"),
        "selected_strategy": coordinator.strategy,
        "test_mode": coordinator.dry_run,
        "powerstream_group_count": len(plan),
        "command_needed_count": totals.get("command_needed_count"),
        "delta_abs_w": totals.get("delta_abs_w"),
        "next_action": next_action.get("summary"),
        "action_type": next_action.get("action_type"),
        "action_state": snapshot_state,
        "snapshot_state": snapshot_state,
        "snapshot_icon": snapshot_icon,
        "flow_phase": flow_phase,
        "can_execute": next_action.get("can_execute"),
        "command_required": next_action.get("command_required"),
        "blocked_by": next_action.get("blocked_by"),
    }


def _powerstream_execution_plan(
    coordinator: EcoFlowEnergyCoordinator,
) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    data = coordinator.data or {}
    settings = _dashboard_settings(coordinator)
    powerstreams = data.get("powerstreams") or {}
    configured = _configured_items(settings, "powerstreams")
    bands = data.get("price_bands") or {}
    price_now = data.get("price_now")
    solar_power = data.get("corrected_solar_power") or 0
    for device in configured:
        serial_value = device.get("serial")
        if not serial_value:
            continue
        serial = str(serial_value)
        item = powerstreams.get(serial, {})
        if not isinstance(item, dict):
            item = {}
        battery_serial = item.get("battery_serial") or device.get("battery_serial")
        battery_name = item.get("battery_name") or _configured_battery_name(
            settings, battery_serial
        )
        battery_soc = item.get("battery_soc")
        if battery_soc is None:
            battery_soc = _battery_soc_for_serial(coordinator, battery_serial)
        battery_free_wh = item.get("battery_free_wh")
        if battery_free_wh is None:
            battery_free_wh = _battery_free_wh_for_serial(
                coordinator, battery_serial, battery_name
            )
        strategy = item.get("group_strategy") or coordinator.powerstream_strategies.get(
            serial, "max_self_use"
        )
        decision_item = {
            **device,
            **item,
            "max_watts": item.get("max_watts") or device.get("max_watts"),
            "battery_soc": battery_soc,
            "battery_free_wh": battery_free_wh,
        }
        decision = powerstream_group_decision(
            strategy,
            decision_item,
            price_now,
            bands,
            float(solar_power or 0),
        )
        current_watts = (
            item.get("target_watts")
            if item.get("target_watts") is not None
            else coordinator.powerstream_targets.get(serial)
        )
        current_watts_known = current_watts is not None
        current_watts_source = item.get("target_watts_source")
        current_watts_verified = bool(
            current_watts_source
            and current_watts_source not in {"command", "strategy_command", "stored_target"}
        )
        suggested_watts = (
            item.get("suggested_watts")
            if item.get("suggested_watts") is not None
            else decision.get("suggested_watts")
        )
        delta_watts = _power_delta_watts(current_watts, suggested_watts)
        suggested_float = _as_float(suggested_watts) or 0
        command_needed = (
            abs(delta_watts) >= 1
            if current_watts_known
            else bool(abs(suggested_float) >= 1)
        )
        plan.append(
            {
                "serial": serial,
                "name": item.get("name") or device.get("name") or serial,
                "strategy": strategy,
                "action": item.get("group_action") or decision.get("group_action"),
                "reason": item.get("decision_reason")
                or decision.get("decision_reason"),
                "command_source": item.get("command_source"),
                "current_watts": current_watts,
                "current_watts_known": current_watts_known,
                "current_watts_source": current_watts_source,
                "current_watts_verified": current_watts_verified,
                "suggested_watts": suggested_watts,
                "delta_watts": delta_watts,
                "command_needed": command_needed,
                "phase": item.get("phase") or device.get("phase"),
                "managed_battery_serial": battery_serial,
                "managed_battery_name": battery_name,
                "managed_battery_soc": battery_soc,
                "managed_battery_free_wh": battery_free_wh,
                "can_charge": item.get("can_charge")
                if item.get("can_charge") is not None
                else decision.get("can_charge"),
                "can_discharge": item.get("can_discharge")
                if item.get("can_discharge") is not None
                else decision.get("can_discharge"),
                "charge_blocker": item.get("charge_blocker")
                or decision.get("charge_blocker"),
                "discharge_blocker": item.get("discharge_blocker")
                or decision.get("discharge_blocker"),
                "strategy_throttled": item.get("strategy_throttled"),
                "strategy_next_update_seconds": item.get(
                    "strategy_next_update_seconds"
                ),
                "strategy_error": item.get("strategy_error"),
                "plan_source": "live" if item else "fallback",
            }
        )
    return plan


def _execution_plan_totals(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    plan = _powerstream_execution_plan(coordinator)
    return {
        "group_count": len(plan),
        "active_group_count": len(
            [item for item in plan if float(item.get("suggested_watts") or 0) > 0]
        ),
        "suggested_total_w": round(
            sum(float(item.get("suggested_watts") or 0) for item in plan), 0
        ),
        "current_total_w": round(
            sum(float(item.get("current_watts") or 0) for item in plan), 0
        ),
        "delta_total_w": round(
            sum(float(item.get("delta_watts") or 0) for item in plan), 0
        ),
        "delta_abs_w": round(
            sum(abs(float(item.get("delta_watts") or 0)) for item in plan), 0
        ),
        "command_needed_count": len(
            [item for item in plan if item.get("command_needed")]
        ),
        "unknown_current_count": len(
            [item for item in plan if not item.get("current_watts_known")]
        ),
        "unverified_current_count": len(
            [item for item in plan if item.get("current_watts_verified") is False]
        ),
    }


def _measurement_state(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    plan = _powerstream_execution_plan(coordinator)
    issues = _powerstream_issue_summary(plan)
    if not plan:
        state = "geen PS"
        reason = "geen PowerStreams ingesteld"
    elif issues.get("error_count"):
        state = "fout"
        reason = f"fout bij {issues.get('first_error_name')}"
    else:
        unknown = [item for item in plan if not item.get("current_watts_known")]
        unverified = [
            item for item in plan if item.get("current_watts_verified") is False
        ]
        verified = [
            item for item in plan if item.get("current_watts_verified") is True
        ]
        if unknown or unverified:
            state = "wacht meting"
            reason = "wacht op gemeten PowerStream-waarde"
        elif len(verified) == len(plan):
            state = "gemeten"
            reason = "alle PowerStream-waarden komen uit telemetrie"
        else:
            state = "beperkt"
            reason = "PowerStream-meetbron is deels onbekend"
    return {
        "state": state,
        "reason": reason,
        "group_count": len(plan),
        "verified_current_count": len(
            [item for item in plan if item.get("current_watts_verified") is True]
        ),
        "unverified_current_count": len(
            [item for item in plan if item.get("current_watts_verified") is False]
        ),
        "unknown_current_count": len(
            [item for item in plan if not item.get("current_watts_known")]
        ),
        "first_unverified_name": next(
            (
                item.get("name")
                for item in plan
                if item.get("current_watts_verified") is False
            ),
            None,
        ),
        "first_unverified_source": next(
            (
                item.get("current_watts_source")
                for item in plan
                if item.get("current_watts_verified") is False
            ),
            None,
        ),
        "first_unknown_name": next(
            (
                item.get("name")
                for item in plan
                if not item.get("current_watts_known")
            ),
            None,
        ),
        "sources": {
            str(item.get("serial")): item.get("current_watts_source")
            for item in plan
        },
        **issues,
    }


def _scenario_confidence(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    data = coordinator.data or {}
    readiness = dashboard_readiness(data, _dashboard_settings(coordinator))
    best = _best_scenario(coordinator)
    measurement = _measurement_state(coordinator)
    readiness_score = _as_float(readiness.get("score")) or 0
    score = readiness_score * 0.45
    reasons: list[str] = []

    if not best.get("key"):
        input_score = 0
        reasons.append("geen scenarioadvies")
    elif best.get("input_ready"):
        input_score = 25
    else:
        input_score = 10
        warnings = best.get("input_warnings") or []
        reasons.append(f"input beperkt: {', '.join(warnings)}" if warnings else "input beperkt")
    score += input_score

    measurement_state = str(measurement.get("state") or "onbekend")
    measurement_score = {
        "gemeten": 20,
        "beperkt": 10,
        "wacht meting": 8,
        "geen PS": 0,
        "fout": 0,
    }.get(measurement_state, 0)
    score += measurement_score
    if measurement_state != "gemeten":
        reasons.append(str(measurement.get("reason") or "PowerStream-meting niet volledig"))

    actionable = scenario_is_actionable(best)
    if actionable:
        score += 10
    else:
        reasons.append(best.get("reason") or "advies niet uitvoerbaar")

    final_score = max(0, min(100, round(score)))
    if final_score >= 85:
        state = "hoog"
    elif final_score >= 60:
        state = "middel"
    else:
        state = "laag"
    return {
        "score": final_score,
        "state": state,
        "readiness_score": readiness.get("score"),
        "input_ready": best.get("input_ready"),
        "measurement_state": measurement_state,
        "best_scenario_key": best.get("key"),
        "best_action": best.get("action"),
        "best_actionable": actionable,
        "reasons": reasons,
        "basis": "45% bronnen, 25% input, 20% PowerStream-meting, 10% uitvoerbaar advies",
    }


def _live_proof(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    readiness = dashboard_readiness(
        coordinator.data or {}, _dashboard_settings(coordinator)
    )
    checks = readiness.get("checks") or []
    ready = [item for item in checks if item.get("status") == "klaar"]
    warnings = [item for item in checks if item.get("status") == "gedeeltelijk"]
    blocking = [item for item in checks if item.get("status") == "actie nodig"]
    data_checks = [item for item in checks if item.get("key") != "execution"]
    ready_data = [item for item in data_checks if item.get("status") == "klaar"]
    execution = next((item for item in checks if item.get("key") == "execution"), {})
    first_missing = (blocking or warnings or [{}])[0]
    return {
        "status": readiness.get("status"),
        "score": readiness.get("score"),
        "ready": readiness.get("ready"),
        "ready_sources": len(ready),
        "warning_sources": len(warnings),
        "blocking_sources": len(blocking),
        "total_sources": len(checks),
        "data_ready": len(ready_data) == len(data_checks) and bool(data_checks),
        "data_ready_sources": len(ready_data),
        "data_total_sources": len(data_checks),
        "execution_status": execution.get("status"),
        "execution_message": execution.get("message"),
        "execution_ready": execution.get("status") == "klaar",
        "execution_details": execution.get("details"),
        "next_step": readiness.get("next_step"),
        "proved_keys": [item.get("key") for item in ready],
        "warning_keys": [item.get("key") for item in warnings],
        "blocking_keys": [item.get("key") for item in blocking],
        "first_missing_key": first_missing.get("key"),
        "first_missing_status": first_missing.get("status"),
        "first_missing_message": first_missing.get("message"),
        "first_missing_label": _dashboard_check_label(str(first_missing.get("key") or "")),
        "source_statuses": {
            str(item.get("key")): item.get("status") for item in checks
        },
        "source_messages": {
            str(item.get("key")): item.get("message") for item in checks
        },
    }


def _live_validation(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    proof = _live_proof(coordinator)
    readiness = dashboard_readiness(
        coordinator.data or {}, _dashboard_settings(coordinator)
    )
    measurement = _measurement_state(coordinator)
    action = _next_dashboard_action(coordinator)
    total_sources = int(proof.get("total_sources") or 0)
    data_ready = bool(proof.get("data_ready"))
    execution_ready = bool(proof.get("execution_ready"))
    blocking_sources = int(proof.get("blocking_sources") or 0)
    warning_sources = int(proof.get("warning_sources") or 0)
    measurement_state = str(measurement.get("state") or "onbekend")
    insight_ready = bool(readiness.get("insight_ready"))
    control_ready = bool(readiness.get("control_ready"))

    if not total_sources:
        state = "geen bewijs"
        summary = "geen live bronchecks beschikbaar"
    elif blocking_sources:
        state = "actie nodig"
        summary = live_missing_summary(proof, readiness.get("next_step"))
    elif insight_ready and not control_ready:
        state = "basis live"
        summary = live_missing_summary(proof, readiness.get("next_step"))
    elif not data_ready:
        state = "data nodig"
        summary = live_missing_summary(
            proof,
            f"{proof.get('data_ready_sources')}/{proof.get('data_total_sources')} "
            "databronnen klaar",
        )
    elif coordinator.dry_run and execution_ready:
        state = "testmodus"
        summary = "data klaar; echte sturing staat nog uit"
    elif execution_ready and measurement_state in {"gemeten", "beperkt"}:
        state = "live klaar"
        summary = "data en sturing bewezen"
    elif execution_ready:
        state = "optimalisatie beperkt"
        summary = str(measurement.get("reason") or "wacht op PowerStream-meting")
    else:
        state = "sturing beperkt"
        summary = str(proof.get("execution_message") or "sturing nog niet bewezen")

    return {
        "state": state,
        "summary": summary,
        "score": readiness.get("score"),
        "insight_ready": insight_ready,
        "control_ready": control_ready,
        "data_ready": data_ready,
        "data_ready_sources": proof.get("data_ready_sources"),
        "data_total_sources": proof.get("data_total_sources"),
        "execution_ready": execution_ready,
        "execution_status": proof.get("execution_status"),
        "execution_message": proof.get("execution_message"),
        "measurement_state": measurement_state,
        "measurement_reason": measurement.get("reason"),
        "blocking_sources": blocking_sources,
        "warning_sources": warning_sources,
        "first_missing_key": proof.get("first_missing_key"),
        "first_missing_label": proof.get("first_missing_label"),
        "first_missing_status": proof.get("first_missing_status"),
        "first_missing_message": proof.get("first_missing_message"),
        "next_step": readiness.get("next_step"),
        "next_action": action.get("summary"),
        "can_execute": action.get("can_execute"),
        "test_mode": coordinator.dry_run,
        "source_statuses": proof.get("source_statuses"),
    }


def _dashboard_problem(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    readiness = dashboard_readiness(
        coordinator.data or {}, _dashboard_settings(coordinator)
    )
    checks = readiness.get("checks") or []
    blocking = next(
        (item for item in checks if item.get("status") == "actie nodig"), None
    )
    warning = next(
        (item for item in checks if item.get("status") == "gedeeltelijk"), None
    )
    problem = blocking or warning
    if not problem:
        return {
            "summary": "alles ok",
            "status": "klaar",
            "check_key": None,
            "message": "alle checks klaar",
            "next_step": readiness.get("next_step"),
            "score": readiness.get("score"),
        }
    status = str(problem.get("status") or "onbekend")
    message = str(problem.get("message") or readiness.get("next_step") or "controleer")
    key = str(problem.get("key") or "check")
    label = _dashboard_check_label(key)
    if status == "actie nodig":
        severity = "blokkeert"
    elif readiness.get("insight_ready"):
        severity = "optimalisatie"
    else:
        severity = "let op"
    return {
        "summary": f"{severity}: {label} - {message}",
        "status": status,
        "severity": severity,
        "check_key": key,
        "label": label,
        "message": message,
        "details": problem.get("details", {}),
        "next_step": readiness.get("next_step"),
        "score": readiness.get("score"),
    }


def _dashboard_check_label(key: str) -> str:
    return {
        "prices": "prijzen",
        "batteries": "batterijen",
        "powerstreams": "PowerStreams",
        "solar": "netto opwek",
        "p1_history": "P1 historie",
        "weather": "weer",
        "scenarios": "scenario's",
        "execution": "sturing",
    }.get(key, key)


def _powerstream_issue_summary(plan: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [item for item in plan if item.get("strategy_error")]
    throttled = [item for item in plan if item.get("strategy_throttled")]
    first_error = errors[0] if errors else {}
    first_throttled = throttled[0] if throttled else {}
    return {
        "error_count": len(errors),
        "first_error_serial": first_error.get("serial"),
        "first_error_name": first_error.get("name"),
        "first_error_message": first_error.get("strategy_error"),
        "throttled_count": len(throttled),
        "first_throttled_serial": first_throttled.get("serial"),
        "first_throttled_name": first_throttled.get("name"),
        "first_throttled_seconds": first_throttled.get(
            "strategy_next_update_seconds"
        ),
    }


def _command_guard_summary(issues: dict[str, Any]) -> str:
    if issues.get("error_count"):
        name = issues.get("first_error_name") or "PowerStream"
        return f"fout bij {name}"
    if issues.get("throttled_count"):
        name = issues.get("first_throttled_name") or "PowerStream"
        seconds = issues.get("first_throttled_seconds")
        suffix = f" ({seconds}s)" if seconds is not None else ""
        return f"wacht op {name}{suffix}"
    return "vrij"


def _next_dashboard_action(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    return next_dashboard_action(
        _powerstream_execution_plan(coordinator),
        dashboard_readiness(coordinator.data or {}, _dashboard_settings(coordinator)),
        coordinator.dry_run,
        coordinator.strategy,
    )


def _setup_state(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    settings = _dashboard_settings(coordinator)
    return setup_state(settings, dry_run=coordinator.dry_run)


def _simple_flow_stage(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    return simple_flow_stage(
        dashboard_readiness(coordinator.data or {}, _dashboard_settings(coordinator)),
        _setup_state(coordinator),
        _next_dashboard_action(coordinator),
        dry_run=coordinator.dry_run,
    )


def _setup_advice(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    setup = _setup_state(coordinator)
    readiness = dashboard_readiness(
        coordinator.data or {}, _dashboard_settings(coordinator)
    )
    if not setup.get("ready_for_basic_insight"):
        state = "basis nodig"
        summary = f"eerst: {setup.get('next_step')}"
    elif not setup.get("ready_for_powerstream_control"):
        state = "basis klaar"
        summary = "basisinzicht werkt; PowerStream is alleen nodig voor sturing"
    elif not setup.get("ready_for_full_optimization"):
        state = "sturen klaar"
        summary = f"sturen kan; optimalisatie beter met {setup.get('next_step')}"
    else:
        state = "optimaal"
        summary = "basis en optimalisatie compleet"
    return {
        "state": state,
        "summary": summary,
        "current_capability": setup.get("current_capability"),
        "setup_state": setup.get("state"),
        "setup_progress": setup.get("progress"),
        "next_setup_step": setup.get("next_step"),
        "next_step_kind": setup.get("next_step_kind"),
        "ready_for_basic_insight": setup.get("ready_for_basic_insight"),
        "ready_for_powerstream_control": setup.get("ready_for_powerstream_control"),
        "ready_for_full_optimization": setup.get("ready_for_full_optimization"),
        "dashboard_readiness": readiness.get("status"),
        "dashboard_score": readiness.get("score"),
        "live_next_step": readiness.get("next_step"),
        "missing_required": setup.get("missing_required"),
        "missing_optional": setup.get("missing_optional"),
        "basic_requirements": setup.get("basic_requirements"),
        "control_requirements": setup.get("control_requirements"),
        "optimization_requirements": setup.get("optimization_requirements"),
        "configured_batteries": setup.get("configured_batteries"),
        "configured_powerstreams": setup.get("configured_powerstreams"),
        "configured_solar_sources": setup.get("configured_solar_sources"),
        "price_source": setup.get("price_source"),
        "price_source_defaulted": setup.get("price_source_defaulted"),
        "price_source_note": (
            "EnergyZero standaard"
            if setup.get("price_source_defaulted")
            else str(setup.get("price_source") or "prijsbron ingesteld")
        ),
        "weather_city": setup.get("weather_city"),
        "dry_run": setup.get("dry_run"),
        "basis": "eerst basisinzicht, daarna PowerStream-sturing, daarna optimalisatie",
    }


def _dashboard_next_user_step(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    return next_user_step(
        dashboard_readiness(coordinator.data or {}, _dashboard_settings(coordinator)),
        _setup_state(coordinator),
        _next_dashboard_action(coordinator),
        dry_run=coordinator.dry_run,
        choice=_scenario_choice_summary(coordinator),
        live_proof=_live_proof(coordinator),
    )


def _powerstream_plan_item(
    coordinator: EcoFlowEnergyCoordinator, serial: str
) -> dict[str, Any]:
    for item in _powerstream_execution_plan(coordinator):
        if str(item.get("serial")) == str(serial):
            return item
    return {}


def _powerstream_plan_attrs(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "current_watts": item.get("current_watts"),
        "current_watts_known": item.get("current_watts_known"),
        "current_watts_source": item.get("current_watts_source"),
        "current_watts_verified": item.get("current_watts_verified"),
        "suggested_watts": item.get("suggested_watts"),
        "delta_watts": item.get("delta_watts"),
        "command_needed": item.get("command_needed"),
        "action": item.get("action"),
        "reason": item.get("reason"),
        "strategy": item.get("strategy"),
        "plan_source": item.get("plan_source"),
        "managed_battery_serial": item.get("managed_battery_serial"),
        "managed_battery_name": item.get("managed_battery_name"),
        "managed_battery_soc": item.get("managed_battery_soc"),
    }


def _configured_items(settings: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [
        item
        for item in settings.get(key, [])
        if isinstance(item, dict)
        and (item.get("serial") or item.get("host") or item.get("device_id"))
    ]


def _configured_live_items(
    configured: list[dict[str, Any]],
    items: dict[str, Any],
    require_values: bool = False,
) -> int:
    count = 0
    for configured_item in configured:
        key = configured_item.get("serial") or configured_item.get("host")
        key = key or configured_item.get("device_id")
        if key is None:
            continue
        item = items.get(str(key))
        if not _is_live_item(item, require_values):
            continue
        count += 1
    return count


def _configured_batteries_with_soc(
    configured: list[dict[str, Any]], batteries: dict[str, Any]
) -> int:
    count = 0
    for configured_item in configured:
        serial = configured_item.get("serial")
        if serial is None:
            continue
        item = batteries.get(str(serial))
        if not _is_live_item(item, require_values=True):
            continue
        values = item.get("values", {}) if isinstance(item, dict) else {}
        if _battery_soc_value(values) is not None:
            count += 1
    return count


def _configured_battery_name(
    settings: dict[str, Any], serial: Any | None
) -> str | None:
    if serial is None:
        return None
    for item in _configured_items(settings, "batteries"):
        if str(item.get("serial")) == str(serial):
            return str(item.get("name") or item.get("serial"))
    return None


def _power_delta_watts(current_watts: Any, suggested_watts: Any) -> float:
    current = _as_float(current_watts)
    suggested = _as_float(suggested_watts)
    if suggested is None:
        return 0.0
    if current is None:
        current = 0.0
    return round(suggested - current, 0)


def _battery_soc_for_serial(
    coordinator: EcoFlowEnergyCoordinator, serial: Any | None
) -> float | None:
    if serial is None:
        return None
    return _battery_soc_value(_battery_values(coordinator, str(serial)))


def _battery_free_wh_for_serial(
    coordinator: EcoFlowEnergyCoordinator,
    serial: Any | None,
    battery_name: Any | None,
) -> float | None:
    if serial is None:
        return None
    values = _battery_values(coordinator, str(serial))
    soc = _battery_soc_value(values)
    capacity = _battery_capacity_wh(values, battery_name)
    if soc is None or capacity is None:
        return None
    available = capacity * float(soc) / 100
    return round(max(0.0, capacity - available), 0)


def _live_items(items: dict[str, Any], require_values: bool = False) -> int:
    count = 0
    for item in items.values():
        if not _is_live_item(item, require_values):
            continue
        count += 1
    return count


def _is_live_item(item: Any, require_values: bool = False) -> bool:
    if not isinstance(item, dict) or item.get("error") or item.get("available") is False:
        return False
    if require_values and not item.get("values"):
        return False
    return True


def _powerstream_values(
    coordinator: EcoFlowEnergyCoordinator, serial: str
) -> dict[str, Any]:
    return (
        (coordinator.data or {})
        .get("powerstreams", {})
        .get(serial, {})
        .get("values", {})
    )


def _powerstream_data(
    coordinator: EcoFlowEnergyCoordinator, serial: str
) -> dict[str, Any]:
    return (coordinator.data or {}).get("powerstreams", {}).get(serial, {})


def _linked_battery_values(
    coordinator: EcoFlowEnergyCoordinator, powerstream_serial: str
) -> dict[str, Any]:
    data = _powerstream_data(coordinator, powerstream_serial)
    battery_serial = data.get("battery_serial")
    if not battery_serial:
        return {}
    return _battery_values(coordinator, str(battery_serial))


def _powerstream_group_available_wh(
    coordinator: EcoFlowEnergyCoordinator, powerstream_serial: str
) -> float | None:
    data = _powerstream_data(coordinator, powerstream_serial)
    soc = data.get("battery_soc")
    capacity = _battery_capacity_wh(
        _linked_battery_values(coordinator, powerstream_serial),
        data.get("battery_name"),
    )
    if soc is None or capacity is None:
        return None
    return round(capacity * float(soc) / 100, 0)


def _powerstream_group_free_wh(
    coordinator: EcoFlowEnergyCoordinator, powerstream_serial: str
) -> float | None:
    data = _powerstream_data(coordinator, powerstream_serial)
    soc = data.get("battery_soc")
    capacity = _battery_capacity_wh(
        _linked_battery_values(coordinator, powerstream_serial),
        data.get("battery_name"),
    )
    if soc is None or capacity is None:
        return None
    available = capacity * float(soc) / 100
    return round(max(0.0, capacity - available), 0)


def _battery_available_kwh(
    values: dict[str, Any], battery_name: Any | None = None
) -> float | None:
    soc = _battery_soc_value(values)
    capacity = _battery_capacity_wh(values, battery_name)
    if soc is None or capacity is None:
        return None
    return round(capacity * float(soc) / 100000, 2)


def _battery_capacity_wh(
    values: dict[str, Any], battery_name: Any | None = None
) -> float | None:
    capacity = _first_value(
        values,
        (
            "cmsBattFullEnergy",
            "ems.fullEnergy",
            "pd.fullEnergy",
            "fullEnergy",
            "fullEnergyWh",
            "batteryFullEnergy",
            "bmsDesignCap",
            "bms_emsStatus.designCap",
            "bms_bmsStatus.designCap",
        ),
    )
    if capacity <= 0:
        return _battery_nominal_capacity_wh(battery_name)
    if capacity < 100:
        capacity = capacity * 1000
    return round(capacity, 0)


def _battery_nominal_capacity_wh(battery_name: Any | None) -> float | None:
    normalized = str(battery_name or "").lower().replace(" ", "")
    if "delta" not in normalized:
        return None
    if "pro3" in normalized or "delta3" in normalized:
        return 8192.0
    if "pro" in normalized:
        return 7200.0
    return None


def _battery_energy_candidates(values: dict[str, Any]) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    for key, value in values.items():
        normalized = _normalize_key(key)
        if any(part in normalized for part in ("energy", "capacity", "designcap", "full")):
            candidates[key] = value
    return dict(sorted(candidates.items())[:30])


def _powerstream_power_candidates(values: dict[str, Any]) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    for key, value in values.items():
        normalized = _normalize_key(key)
        if "watt" in normalized or "power" in normalized:
            candidates[key] = value
    return dict(sorted(candidates.items())[:20])


def _status_label(device_type: str) -> str:
    return {
        "battery": "batterijstatus",
        "powerstream": "PowerStream",
        "smart_plug": "Smart Plug",
    }.get(device_type, "EcoFlow")


def _strategy_guide(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    selected = coordinator.strategy
    selected_key = _selected_scenario_key(selected)
    best = _best_scenario(coordinator)
    guides = {
        STRATEGY_SELF_USE: {
            "label": "Eigen gebruik",
            "summary": "gebruik accu om dure netstroom te vermijden",
            "when": "standaardkeuze voor lagere energiekosten met weinig risico",
            "does": "laadt bij netto zon of lage prijs en ontlaadt bij dure stroom",
            "risk": "minder agressieve winst dan handelen",
        },
        STRATEGY_EXPORT: {
            "label": "Handelen",
            "summary": "stuur op prijsverschil en teruglevering",
            "when": "als opbrengst belangrijker is dan rustige accucycli",
            "does": "laadt bij goedkoop/zon en levert meer terug bij dure uren",
            "risk": "meer accugebruik en afhankelijker van prijsdata",
        },
        STRATEGY_BUFFER_50: {
            "label": "Buffer 50%",
            "summary": "houd altijd ongeveer halve accu over",
            "when": "als back-upreserve belangrijk is",
            "does": "levert alleen terug boven de reserve en bewaakt de ondergrens",
            "risk": "laat soms besparing of handel liggen",
        },
        STRATEGY_IDLE: {
            "label": "Uit",
            "summary": "geen automatische sturing",
            "when": "voor testen, onderhoud of handmatige bediening",
            "does": "zet automatische strategie uit en stuurt PowerStreams naar 0 W",
            "risk": "geen automatische optimalisatie",
        },
    }
    selected_guide = guides.get(selected, guides[STRATEGY_IDLE])
    return {
        "selected_strategy": selected,
        "selected_scenario_key": selected_key,
        "selected_label": selected_guide["label"],
        "selected_summary": selected_guide["summary"],
        "selected_when": selected_guide["when"],
        "selected_does": selected_guide["does"],
        "selected_risk": selected_guide["risk"],
        "best_scenario_key": best.get("key"),
        "best_label": best.get("label"),
        "best_action": best.get("action"),
        "best_reason": best.get("reason"),
        "best_actionable": scenario_is_actionable(best),
        "guides": [
            {"strategy": key, **value}
            for key, value in guides.items()
        ],
        "docs": "docs/ontwikkeling.md",
    }


def _device_attrs(device_type: str, serial: str, sensor_role: str) -> dict[str, Any]:
    return {
        "eec_device_type": device_type,
        "eec_sensor_role": sensor_role,
        "serial": serial,
    }


def _apply_device_entity_label(
    entity: BaseSensor, device_name: str, label: str, object_suffix: str
) -> None:
    """Keep device entities short while preserving stable readable object ids."""
    entity._attr_has_entity_name = True
    entity._attr_name = label
    entity._attr_suggested_object_id = slugify(
        f"{LEGACY_DASHBOARD_OBJECT_PREFIX}_{device_name}_{object_suffix}"
    )


def _ecoflow_device_info(serial: str, name: str, device_type: str) -> dict[str, Any]:
    return {
        "identifiers": {(DOMAIN, f"ecoflow_{serial}")},
        "name": name,
        "manufacturer": "EcoFlow",
        "model": _device_model(device_type),
        "via_device": (DOMAIN, "controller"),
    }


def _homewizard_device_info(host: str, name: str) -> dict[str, Any]:
    return {
        "identifiers": {(DOMAIN, f"homewizard_{host}")},
        "name": name,
        "manufacturer": "HomeWizard",
        "model": "Energy meter",
        "configuration_url": _host_url(host),
        "via_device": (DOMAIN, "controller"),
    }


def _host_url(host: str) -> str:
    if host.startswith(("http://", "https://")):
        return host
    return f"http://{host}"


def _device_model(device_type: str) -> str:
    return {
        "battery": "Delta battery",
        "powerstream": "PowerStream",
        "smart_plug": "Smart Plug",
    }.get(device_type, "EcoFlow device")


def _first_value(values: dict[str, Any], keys: tuple[str, ...]) -> float:
    for key in keys:
        numeric = _to_float(values.get(key))
        if numeric is not None:
            return numeric
    return 0.0


def _battery_net_power(coordinator: EcoFlowEnergyCoordinator, serial: str) -> float:
    values = _battery_values(coordinator, serial)
    charge = _battery_charge_power(values)
    discharge = _battery_discharge_power(values)
    return round(discharge - charge, 1)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _normalize_key(key: str) -> str:
    return key.lower().replace("_", "").replace("-", "").replace(".", "")


def _looks_like_power_key(normalized_key: str) -> bool:
    return any(
        part in normalized_key
        for part in ("watt", "power", "pow")
    )


def _looks_like_live_power_key(normalized_key: str) -> bool:
    if not _looks_like_power_key(normalized_key):
        return False
    return not any(
        part in normalized_key
        for part in (
            "max",
            "min",
            "limit",
            "design",
            "fullenergy",
            "remain",
            "remtime",
            "standby",
            "soc",
            "soh",
            "temp",
        )
    )
