"""Sensors for EcoFlow Energy Control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    APP_NAME,
    APP_VERSION,
    DOMAIN,
    LEGACY_DASHBOARD_OBJECT_PREFIX,
    STRATEGY_BUFFER_50,
    STRATEGY_EXPORT,
    STRATEGY_IDLE,
    STRATEGY_SELF_USE,
)
from .coordinator import EcoFlowEnergyCoordinator
from .health import dashboard_readiness, source_summary
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
        CorrectedSolarPowerSensor(coordinator),
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
        BestScenarioSensor(coordinator),
        ScenarioAlignmentSensor(coordinator),
        ScenarioChoiceSummarySensor(coordinator),
        DecisionContextSensor(coordinator),
        FlowReadySensor(coordinator),
        FlowSnapshotSensor(coordinator),
        FlowPhaseSensor(coordinator),
        FlowSummarySensor(coordinator),
        FlowValueRateSensor(coordinator),
        FlowBestPowerSensor(coordinator),
        FlowBestDayValueSensor(coordinator),
        FlowBestPeriodValueSensor(coordinator),
        FlowScenarioInputSensor(coordinator),
        FlowConfidenceScoreSensor(coordinator),
        FlowConfidenceReasonSensor(coordinator),
        FlowChoiceDeltaSensor(coordinator),
        FlowChoiceStateSensor(coordinator),
        FlowStartStateSensor(coordinator),
        FlowAutoModeSensor(coordinator),
        FlowExecutionPlanSensor(coordinator),
        FlowMeasurementStateSensor(coordinator),
        FlowNextCommandSensor(coordinator),
        FlowActionStateSensor(coordinator),
        FlowCommandDeltaSensor(coordinator),
        FlowCommandNeededSensor(coordinator),
        FlowStartReasonSensor(coordinator),
        DashboardOverviewSensor(coordinator),
        DashboardSetupSensor(coordinator),
        DashboardSourceSummarySensor(coordinator),
        DashboardProblemSensor(coordinator),
        DashboardLiveProofSensor(coordinator),
        DashboardReadinessSensor(coordinator),
        DashboardReadinessScoreSensor(coordinator),
        DashboardNextStepSensor(coordinator),
        DashboardCheckSensor(coordinator, "prices", "prijzen"),
        DashboardCheckSensor(coordinator, "batteries", "batterijen"),
        DashboardCheckSensor(coordinator, "powerstreams", "PowerStreams"),
        DashboardCheckSensor(coordinator, "solar", "netto opwek"),
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
                ]
            )
    async_add_entities(entities)


class BaseSensor(CoordinatorEntity[EcoFlowEnergyCoordinator], SensorEntity):
    """Base sensor."""

    _attr_has_entity_name = True

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
        if action.get("action_type") == "test_mode":
            return "testmodus"
        if action.get("action_type") == "needs_data":
            return "data nodig"
        if action.get("action_type") == "idle":
            return "scenario uit"
        if action.get("can_execute"):
            return "kan sturen"
        if action.get("action_type") in {"wait", "none"}:
            return "wacht"
        if action.get("action_type") == "error":
            return "fout"
        return "stand-by"

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


class DashboardSetupSensor(BaseSensor):
    """Compact status showing whether the minimal local setup is complete."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_setup", "setup")

    @property
    def native_value(self) -> str:
        return str(_setup_state(self.coordinator).get("state"))

    @property
    def icon(self) -> str:
        return {
            "compleet": "mdi:check-circle",
            "beperkt": "mdi:progress-wrench",
            "actie nodig": "mdi:alert-circle",
        }.get(self.native_value, "mdi:cog")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_setup",
            **_setup_state(self.coordinator),
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
        super().__init__(coordinator, "dashboard_problem", "probleem")

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


class DashboardNextStepSensor(BaseSensor):
    """Most useful next action for the simple dashboard flow."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "dashboard_next_step", "volgende stap")

    @property
    def native_value(self) -> str:
        return str(
            dashboard_readiness(
                self.coordinator.data or {}, _dashboard_settings(self.coordinator)
            )["next_step"]
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        readiness = dashboard_readiness(
            self.coordinator.data or {}, _dashboard_settings(self.coordinator)
        )
        return {
            "eec_device_type": "dashboard",
            "eec_sensor_role": "dashboard_next_step",
            "status": readiness["status"],
            "score": readiness["score"],
            "blocking": readiness["blocking"],
            "warnings": readiness["warnings"],
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
        super().__init__(coordinator, f"{serial}_soc", f"{name} SoC")
        self._serial = serial
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
        super().__init__(
            coordinator, f"{serial}_available_kwh", f"{name} beschikbaar"
        )
        self._serial = serial
        self._name = name
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
        super().__init__(coordinator, f"{serial}_available_eur", f"{name} waarde")
        self._serial = serial
        self._name = name
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
        super().__init__(
            coordinator, f"{serial}_api_status", f"{_status_label(device_type)} {name}"
        )
        self._serial = serial
        self._device_type = device_type
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
        super().__init__(coordinator, f"{serial}_charge_power", f"{name} laadvermogen")
        self._serial = serial
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
        super().__init__(
            coordinator, f"{serial}_discharge_power", f"{name} ontlaadvermogen"
        )
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_charge_source", f"{name} laadbron")
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_net_power", f"{name} netto vermogen")
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_mode", f"{name} status")
        self._serial = serial
        self._attr_device_info = _ecoflow_device_info(serial, name, "battery")

    @property
    def native_value(self) -> str:
        net = _battery_net_power(self.coordinator, self._serial)
        if net > 20:
            return "ontladen"
        if net < -20:
            return "laden"
        return "stand-by"

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
        super().__init__(coordinator, f"{serial}_powerstream_power", f"{name} vermogen")
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_powerstream_mode", f"{name} status")
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_group_suggested_watts", f"{name} advies")
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_group_delta_watts", f"{name} nog")
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_group_command_status", f"{name} bijsturen")
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_group_battery_soc", f"{name} accu")
        self._serial = serial
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
        super().__init__(
            coordinator, f"{serial}_group_available_wh", f"{name} beschikbaar"
        )
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_group_free_wh", f"{name} ruimte")
        self._serial = serial
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
        super().__init__(coordinator, f"{serial}_group_action", f"{name} actie")
        self._serial = serial
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
        super().__init__(coordinator, f"homewizard_{host}_status", f"{name} status")
        self._host = host
        self._name = name
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
        super().__init__(coordinator, f"homewizard_{host}_power", f"{name} vermogen")
        self._host = host
        self._name = name
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
            f"{name} {phase.upper()} vermogen",
        )
        self._host = host
        self._name = name
        self._phase = phase
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
        if soc is None or capacity is None:
            batteries.append(
                {
                    "serial": serial,
                    "name": name,
                    "soc": soc,
                    "capacity_kwh": round(capacity / 1000, 2) if capacity else None,
                    "available_kwh": None,
                    "free_kwh": None,
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
        "battery_count": len(batteries),
        "batteries": batteries,
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
    if readiness.get("status") != "klaar":
        summary = f"{readiness.get('status')}: {readiness.get('next_step')}"
    else:
        summary = (
            f"{best_label}: {best_action}; {available:.1f} kWh; "
            f"{price_context}; {solar_context}; nog {delta:.0f} W"
        )
    return {
        "summary": summary,
        "readiness_status": readiness.get("status"),
        "readiness_score": readiness.get("score"),
        "next_step": readiness.get("next_step"),
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
        "source_statuses": {
            str(item.get("key")): item.get("status") for item in checks
        },
        "source_messages": {
            str(item.get("key")): item.get("message") for item in checks
        },
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
            "summary": "geen probleem",
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
    severity = "blokkeert" if status == "actie nodig" else "let op"
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


def _next_dashboard_action(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    return next_dashboard_action(
        _powerstream_execution_plan(coordinator),
        dashboard_readiness(coordinator.data or {}, _dashboard_settings(coordinator)),
        coordinator.dry_run,
        coordinator.strategy,
    )


def _setup_state(coordinator: EcoFlowEnergyCoordinator) -> dict[str, Any]:
    settings = _dashboard_settings(coordinator)
    batteries = _configured_items(settings, "batteries")
    powerstreams = _configured_items(settings, "powerstreams")
    homewizard = _configured_items(settings, "homewizard_meters")
    sma = _configured_items(settings, "sma_inverters")
    solar_sources = homewizard + sma
    missing: list[str] = []
    optional: list[str] = []
    if not batteries:
        missing.append("batterij toevoegen")
    if not powerstreams:
        optional.append("PowerStream toevoegen")
    if not solar_sources:
        optional.append("zonmeter toevoegen")
    if not settings.get("price_source") and not settings.get("price_url"):
        missing.append("prijsbron instellen")
    if not settings.get("weather_city"):
        optional.append("weerstad instellen")
    if missing:
        state = "actie nodig"
        next_step = missing[0]
    elif optional:
        state = "beperkt"
        next_step = optional[0]
    else:
        state = "compleet"
        next_step = "basisconfiguratie compleet"
    return {
        "state": state,
        "next_step": next_step,
        "missing_required": missing,
        "missing_optional": optional,
        "configured_batteries": len(batteries),
        "configured_powerstreams": len(powerstreams),
        "configured_solar_sources": len(solar_sources),
        "configured_homewizard_meters": len(homewizard),
        "configured_sma_inverters": len(sma),
        "price_source": settings.get("price_source"),
        "custom_price_url": bool(settings.get("price_url")),
        "weather_city": settings.get("weather_city"),
        "dry_run": coordinator.dry_run,
        "basis": "minimaal: batterij en prijsbron; optimaal: PowerStream, zonmeter en weerstad",
    }


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


def _device_attrs(device_type: str, serial: str, sensor_role: str) -> dict[str, Any]:
    return {
        "eec_device_type": device_type,
        "eec_sensor_role": sensor_role,
        "serial": serial,
    }


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
