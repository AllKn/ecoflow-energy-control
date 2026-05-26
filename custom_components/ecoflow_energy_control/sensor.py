"""Sensors for EcoFlow Energy Control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import APP_NAME, DOMAIN
from .coordinator import EcoFlowEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcoFlowEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
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
        host = device.get("host")
        if host:
            name = device.get("name", host)
            entities.extend(
                [
                    HomeWizardMeterStatusSensor(coordinator, host, name),
                    HomeWizardMeterPowerSensor(coordinator, host, name),
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
        values = (
            (self.coordinator.data or {}).get("batteries", {})
            .get(self._serial, {})
            .get("values", {})
        )
        return values.get("pd.soc") or values.get("soc")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _device_attrs("battery", self._serial, "soc")


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
                    "soc": values.get("pd.soc") or values.get("soc"),
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
                    "phase": item.get("phase") if item else None,
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
        return _device_attrs("powerstream", self._serial, "power")


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
        return _device_attrs("powerstream", self._serial, "mode")


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
