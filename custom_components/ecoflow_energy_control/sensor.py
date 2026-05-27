"""Sensors for EcoFlow Energy Control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import APP_NAME, APP_VERSION, DOMAIN
from .coordinator import EcoFlowEnergyCoordinator


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
        WeatherSolarForecastSensor(coordinator, 4),
        WeatherSolarForecastSensor(coordinator, 12),
        WeatherSolarForecastSensor(coordinator, 24),
        ExpectedSavingsSensor(coordinator),
        StatusSensor(coordinator),
        LastActionSensor(coordinator),
    ]
    for scenario_key, label in SCENARIOS.items():
        entities.extend(
            [
                ScenarioActionSensor(coordinator, scenario_key, label),
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
                    PowerStreamGroupBatterySocSensor(coordinator, serial, name),
                    PowerStreamGroupAvailableEnergySensor(coordinator, serial, name),
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
        return {
            "prices": summary.get("chart", []),
            "price_count": len(summary.get("chart", [])),
            "raw_price_count": len(data.get("prices", [])),
            "price_error": (data.get("errors") or {}).get("prices"),
            "minimum": summary.get("min"),
            "minimum_start": summary.get("min_start"),
            "maximum": summary.get("max"),
            "maximum_start": summary.get("max_start"),
        }


class VersionSensor(BaseSensor):
    """Loaded integration version."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "version", "versie")

    @property
    def native_value(self) -> str:
        return APP_VERSION


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


class HomeWizardSolarPowerSensor(BaseSensor):
    """Raw HomeWizard solar power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "homewizard_solar_power", "HomeWizard opwek ruw")

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("homewizard_solar_power") or 0)


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
        return {
            "city": weather.get("city"),
            "provider": weather.get("provider"),
            "unit_note": "verwachte Wh per kWp opgesteld vermogen",
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
            "horizon": "24h",
            "basis": "per kWp, op huidige stroomprijs",
            "solar_24h_wh_kwp": weather.get("solar_next_24h_wh_kwp"),
            "price_now": (self.coordinator.data or {}).get("price_now"),
        }


class CheapBandSensor(BaseSensor):
    """Automatic cheap price band sensor."""

    _attr_native_unit_of_measurement = "EUR/kWh"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "cheap_band", "goedkope prijsgrens")

    @property
    def native_value(self) -> float | None:
        return ((self.coordinator.data or {}).get("price_bands") or {}).get("cheap")


class ExpensiveBandSensor(BaseSensor):
    """Automatic expensive price band sensor."""

    _attr_native_unit_of_measurement = "EUR/kWh"

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "expensive_band", "dure prijsgrens")

    @property
    def native_value(self) -> float | None:
        return ((self.coordinator.data or {}).get("price_bands") or {}).get("expensive")


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
            "managed_battery_serial": data.get("battery_serial"),
            "managed_battery_name": data.get("battery_name"),
            "managed_battery_soc": data.get("battery_soc"),
            "phase": data.get("phase"),
            "power_candidates": _powerstream_power_candidates(values),
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
            "strategy_throttled": data.get("strategy_throttled"),
            "strategy_next_update_seconds": data.get("strategy_next_update_seconds"),
            "strategy_error": data.get("strategy_error"),
            "managed_battery_name": data.get("battery_name"),
            "managed_battery_soc": data.get("battery_soc"),
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
            "errors": data.get("errors", {}),
            "ecoflow_devices": data.get("ecoflow_devices", []),
            "last_powerstream_command": data.get("last_powerstream_command"),
            "last_powerstream_error": data.get("last_powerstream_error"),
        }


class LastActionSensor(BaseSensor):
    """Last controller action."""

    def __init__(self, coordinator: EcoFlowEnergyCoordinator) -> None:
        super().__init__(coordinator, "last_action", "laatste actie")

    @property
    def native_value(self) -> str | None:
        return (self.coordinator.data or {}).get("last_action")


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
        return max(0.0, explicit)
    return max(0.0, _classified_battery_power(values, "solar_charge"))


def _battery_dc_charge_power(values: dict[str, Any]) -> float:
    return max(
        0.0,
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
        ),
    )


def _battery_unclassified_input_power(values: dict[str, Any]) -> float:
    return max(
        0.0,
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
        return max(0.0, explicit)
    return max(0.0, _classified_battery_power(values, "discharge"))


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
    return {
        "eec_device_type": "scenario",
        "eec_scenario": scenario_key,
        "eec_sensor_role": f"scenario_{sensor_role}",
        "label": data.get("label", SCENARIOS.get(scenario_key, scenario_key)),
        "action": data.get("action"),
        "power_w": data.get("power_w"),
        "eur_per_hour": data.get("eur_per_hour"),
        "day_eur": data.get("day_eur"),
        "week_eur": data.get("week_eur"),
        "month_eur": data.get("month_eur"),
        "battery_soc": data.get("battery_soc"),
        "price_eur_kwh": data.get("price_eur_kwh"),
    }


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
