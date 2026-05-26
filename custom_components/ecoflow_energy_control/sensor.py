"""Sensors for EcoFlow Energy Control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
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
                    BatteryChargePowerSensor(coordinator, serial, name),
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
                    HomeWizardMeterImportEnergySensor(coordinator, host, name),
                    HomeWizardMeterExportEnergySensor(coordinator, host, name),
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
        return {
            "start": ((self.coordinator.data or {}).get("price_summary") or {}).get(
                "min_start"
            )
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
        return {
            "start": ((self.coordinator.data or {}).get("price_summary") or {}).get(
                "max_start"
            )
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
            "soc_candidates": _battery_soc_candidates(values),
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
            "error": item.get("error") if item else None,
        }
        if self._device_type == "battery":
            attrs.update(
                {
                    "soc": _battery_soc_value(values),
                    "soc_candidates": _battery_soc_candidates(values),
                    "charge_w": _first_value(
                        values,
                        ("pd.inputWatts", "inv.inputWatts", "inputWatts", "chargeWatts"),
                    ),
                    "discharge_w": _first_value(
                        values,
                        (
                            "pd.outputWatts",
                            "pd.invOutWatts",
                            "outputWatts",
                            "dischargeWatts",
                        ),
                    ),
                    "net_w": _battery_net_power(self.coordinator, self._serial),
                }
            )
        if self._device_type == "powerstream":
            attrs.update(
                {
                    "target_w": float(item.get("target_watts") or 0) if item else 0,
                    "raw_target_w": float(item.get("raw_target_watts") or 0) if item else 0,
                    "phase": item.get("phase") if item else None,
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
        return max(
            0.0,
            _first_value(
                _battery_values(self.coordinator, self._serial),
                ("pd.inputWatts", "inv.inputWatts", "inputWatts", "chargeWatts"),
            ),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _device_attrs("battery", self._serial, "charge_power")


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
        return max(
            0.0,
            _first_value(
                _battery_values(self.coordinator, self._serial),
                ("pd.outputWatts", "pd.invOutWatts", "outputWatts", "dischargeWatts"),
            ),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _device_attrs("battery", self._serial, "discharge_power")


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
        return _device_attrs("battery", self._serial, "net_power")


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
        values = _powerstream_values(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "power"),
            "telemetry_fields": len(values),
            "telemetry_keys": sorted(values.keys())[:40],
            "raw_target_w": data.get("raw_target_watts"),
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
        values = _powerstream_values(self.coordinator, self._serial)
        return {
            **_device_attrs("powerstream", self._serial, "mode"),
            "telemetry_fields": len(values),
            "telemetry_keys": sorted(values.keys())[:40],
            "raw_target_w": data.get("raw_target_watts"),
            "power_candidates": _powerstream_power_candidates(values),
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


class HomeWizardMeterImportEnergySensor(BaseSensor):
    """HomeWizard cumulative imported energy."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = "energy"
    _attr_state_class = "total_increasing"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, host: str, name: str
    ) -> None:
        super().__init__(coordinator, f"homewizard_{host}_import_kwh", f"{name} import")
        self._host = host
        self._name = name
        self._attr_device_info = _homewizard_device_info(host, name)

    @property
    def native_value(self) -> float | None:
        value = self._meter_data().get("total_power_import_kwh")
        return float(value) if value is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "homewizard",
            "eec_sensor_role": "energy_import",
            "host": self._host,
        }

    def _meter_data(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("homewizard_meters", {})
        return data.get(self._name, {}) or data.get(self._host, {})


class HomeWizardMeterExportEnergySensor(BaseSensor):
    """HomeWizard cumulative exported energy."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = "energy"
    _attr_state_class = "total_increasing"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, host: str, name: str
    ) -> None:
        super().__init__(coordinator, f"homewizard_{host}_export_kwh", f"{name} export")
        self._host = host
        self._name = name
        self._attr_device_info = _homewizard_device_info(host, name)

    @property
    def native_value(self) -> float | None:
        value = self._meter_data().get("total_power_export_kwh")
        return float(value) if value is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "eec_device_type": "homewizard",
            "eec_sensor_role": "energy_export",
            "host": self._host,
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
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if 0 <= numeric <= 100:
            return numeric
    return None


def _battery_soc_candidates(values: dict[str, Any]) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    for key, value in values.items():
        normalized = key.lower().replace("_", "").replace("-", "")
        if "soc" in normalized or "batterylevel" in normalized:
            candidates[key] = value
    return dict(sorted(candidates.items())[:20])


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


def _powerstream_power_candidates(values: dict[str, Any]) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    for key, value in values.items():
        normalized = key.lower().replace("_", "").replace("-", "")
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
        value = values.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _battery_net_power(coordinator: EcoFlowEnergyCoordinator, serial: str) -> float:
    values = _battery_values(coordinator, serial)
    charge = _first_value(
        values, ("pd.inputWatts", "inv.inputWatts", "inputWatts", "chargeWatts")
    )
    discharge = _first_value(
        values, ("pd.outputWatts", "pd.invOutWatts", "outputWatts", "dischargeWatts")
    )
    return round(discharge - charge, 1)
