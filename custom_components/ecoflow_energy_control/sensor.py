"""Sensors for EcoFlow Energy Control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
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
                    PowerStreamTargetSensor(coordinator, serial, name),
                    PowerStreamModeSensor(coordinator, serial, name),
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
            "name": "EcoFlow Energy Control Applicatie",
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
    """Lowest upcoming Quatt/EPEX price."""

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
    """Highest upcoming Quatt/EPEX price."""

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

    @property
    def native_value(self) -> Any:
        values = (
            (self.coordinator.data or {}).get("batteries", {})
            .get(self._serial, {})
            .get("values", {})
        )
        return values.get("pd.soc") or values.get("soc")


class BatteryChargePowerSensor(BaseSensor):
    """Battery charge power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_charge_power", f"{name} laadvermogen")
        self._serial = serial

    @property
    def native_value(self) -> float:
        return max(
            0.0,
            _first_value(
                _battery_values(self.coordinator, self._serial),
                ("pd.inputWatts", "inv.inputWatts", "inputWatts", "chargeWatts"),
            ),
        )


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

    @property
    def native_value(self) -> float:
        return max(
            0.0,
            _first_value(
                _battery_values(self.coordinator, self._serial),
                ("pd.outputWatts", "pd.invOutWatts", "outputWatts", "dischargeWatts"),
            ),
        )


class BatteryNetPowerSensor(BaseSensor):
    """Battery net power: positive means discharging, negative means charging."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_net_power", f"{name} netto vermogen")
        self._serial = serial

    @property
    def native_value(self) -> float:
        return _battery_net_power(self.coordinator, self._serial)


class BatteryModeSensor(BaseSensor):
    """Battery direction."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_mode", f"{name} status")
        self._serial = serial

    @property
    def native_value(self) -> str:
        net = _battery_net_power(self.coordinator, self._serial)
        if net > 20:
            return "ontladen"
        if net < -20:
            return "laden"
        return "stand-by"


class PowerStreamTargetSensor(BaseSensor):
    """PowerStream target/export power."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = "power"

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_powerstream_power", f"{name} vermogen")
        self._serial = serial

    @property
    def native_value(self) -> float:
        data = (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
        return float(data.get("target_watts") or 0)


class PowerStreamModeSensor(BaseSensor):
    """PowerStream status."""

    def __init__(
        self, coordinator: EcoFlowEnergyCoordinator, serial: str, name: str
    ) -> None:
        super().__init__(coordinator, f"{serial}_powerstream_mode", f"{name} status")
        self._serial = serial

    @property
    def native_value(self) -> str:
        data = (self.coordinator.data or {}).get("powerstreams", {}).get(self._serial, {})
        watts = float(data.get("target_watts") or 0)
        if watts > 20:
            return "terugleveren"
        if watts < -20:
            return "laden"
        return "stand-by"


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
