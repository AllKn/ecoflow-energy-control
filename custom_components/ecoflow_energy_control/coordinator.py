"""Coordinator and local control policy."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api.ecoflow import EcoFlowCloudClient, render_template_dict
from .api.homewizard import read_homewizard_meter
from .api.prices import current_price, fetch_prices, price_bands
from .api.sma_cloud import read_sma_device
from .const import (
    CONF_ACCESS_KEY,
    CONF_BATTERIES,
    CONF_DRY_RUN,
    CONF_ECOFLOW_HOST,
    CONF_HOMEWIZARD_METERS,
    CONF_POWERSTREAMS,
    CONF_PRICE_URL,
    CONF_SECRET_KEY,
    CONF_SMA_API_HOST,
    CONF_SMA_ENDPOINT,
    CONF_SMA_INVERTERS,
    CONF_SMA_PLANT_ID,
    CONF_SMA_TOKEN,
    CONF_SMART_PLUGS,
    DEFAULT_ECOFLOW_HOST,
    DEFAULT_PRICE_URL,
    DEFAULT_SMA_API_HOST,
    DEFAULT_SMA_ENDPOINT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    STRATEGY_IDLE,
)

_LOGGER = logging.getLogger(__name__)


class EcoFlowEnergyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Collect data and apply local policy."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.settings = {**entry.data, **entry.options}
        self.session = async_get_clientsession(hass)
        self.ecoflow = EcoFlowCloudClient(
            self.session,
            self.settings.get(CONF_ECOFLOW_HOST, DEFAULT_ECOFLOW_HOST),
            self.settings[CONF_ACCESS_KEY],
            self.settings[CONF_SECRET_KEY],
        )
        self.strategy = STRATEGY_IDLE
        self.export_watts = 600
        self.self_use_watts = 0
        self.solar_plug_threshold_watts = 1200
        self.powerstream_targets: dict[str, int] = {}
        self.dry_run = bool(self.settings.get(CONF_DRY_RUN, True))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        settings = {**self.entry.data, **self.entry.options}
        prices = await fetch_prices(
            self.session, settings.get(CONF_PRICE_URL, DEFAULT_PRICE_URL)
        )
        price_now = current_price(prices, dt_util.now())
        bands = price_bands(prices)

        batteries = {}
        for device in settings.get(CONF_BATTERIES, []):
            serial = device.get("serial")
            if not serial or "VUL_HIER" in serial:
                continue
            try:
                response = await self.ecoflow.get_device_quotas(
                    serial, device.get("quotas")
                )
                batteries[serial] = {
                    "name": device.get("name", serial),
                    "response": response,
                    "values": _extract_values(response),
                }
            except Exception as err:  # noqa: BLE001
                batteries[serial] = {"name": device.get("name", serial), "error": str(err)}

        inverters = {}
        sma_token = settings.get(CONF_SMA_TOKEN)
        sma_plant_id = settings.get(CONF_SMA_PLANT_ID)
        for item in settings.get(CONF_SMA_INVERTERS, []):
            device_id = item.get("device_id")
            if not sma_token or not sma_plant_id or not device_id:
                continue
            try:
                name = item.get("name", device_id)
                inverters[name] = await read_sma_device(
                    self.session,
                    settings.get(CONF_SMA_API_HOST, DEFAULT_SMA_API_HOST),
                    sma_token,
                    sma_plant_id,
                    item,
                    settings.get(CONF_SMA_ENDPOINT, DEFAULT_SMA_ENDPOINT),
                )
            except Exception as err:  # noqa: BLE001
                inverters[item.get("name", device_id)] = {
                    "available": False,
                    "error": str(err),
                }

        solar_power = sum(
            float(values.get("ac_power_w") or 0) for values in inverters.values()
        )
        homewizard_meters = {}
        homewizard_solar_power = 0.0
        homewizard_phase_power = {"l1": 0.0, "l2": 0.0, "l3": 0.0}
        for item in settings.get(CONF_HOMEWIZARD_METERS, []):
            host = item.get("host")
            if not host:
                continue
            try:
                reading = await read_homewizard_meter(self.session, item)
                name = item.get("name", host)
                homewizard_meters[name] = reading
                if reading.get("role") == "solar_total":
                    active_power = float(reading.get("active_power_w") or 0)
                    homewizard_solar_power += abs(active_power)
                    for phase, watts in reading.get("phase_power_w", {}).items():
                        homewizard_phase_power[phase] += abs(float(watts or 0))
            except Exception as err:  # noqa: BLE001
                homewizard_meters[item.get("name", host)] = {
                    "available": False,
                    "error": str(err),
                }

        powerstream_export = self._tracked_powerstream_export()
        corrected_homewizard_solar = max(0.0, homewizard_solar_power - powerstream_export)
        corrected_phase_power = {
            phase: max(0.0, watts - self._tracked_powerstream_export(phase))
            for phase, watts in homewizard_phase_power.items()
        }
        effective_solar_power = corrected_homewizard_solar if homewizard_meters else solar_power

        return {
            "price_now": price_now,
            "price_bands": bands,
            "prices": prices,
            "batteries": batteries,
            "inverters": inverters,
            "homewizard_meters": homewizard_meters,
            "solar_power": solar_power,
            "homewizard_solar_power": homewizard_solar_power,
            "powerstream_export_w": powerstream_export,
            "corrected_solar_power": effective_solar_power,
            "corrected_phase_power": corrected_phase_power,
            "strategy": self.strategy,
            "dry_run": self.dry_run,
            "last_action": self.data.get("last_action") if self.data else None,
        }

    async def async_set_powerstream_watts(self, serial: str, watts: int) -> None:
        """Set a PowerStream output target using configured command template."""
        device = self._powerstream(serial)
        watts = max(0, min(watts, int(device.get("max_watts", watts))))
        command = render_template_dict(device["command"], {"watts": watts})
        if self.dry_run:
            self.async_set_updated_data(
                {**(self.data or {}), "last_action": f"dry-run {serial} -> {watts} W"}
            )
            return
        await self.ecoflow.set_device_command(serial, command)
        self.powerstream_targets[serial] = watts
        self.async_set_updated_data(
            {**(self.data or {}), "last_action": f"{serial} -> {watts} W"}
        )

    async def async_apply_strategy(self) -> None:
        """Apply the currently selected simple price strategy."""
        price_now = (self.data or {}).get("price_now")
        bands = (self.data or {}).get("price_bands") or {}

        if price_now is not None and self.strategy != STRATEGY_IDLE:
            target = self.self_use_watts
            cheap = bands.get("cheap")
            expensive = bands.get("expensive")
            if cheap is not None and price_now <= cheap:
                target = 0
            elif expensive is not None and price_now >= expensive:
                target = self.export_watts

            for device in self.settings.get(CONF_POWERSTREAMS, []):
                serial = device.get("serial")
                if serial and "VUL_HIER" not in serial:
                    await self.async_set_powerstream_watts(serial, target)

        solar_power = float((self.data or {}).get("corrected_solar_power") or 0)
        plug_on = solar_power >= self.solar_plug_threshold_watts
        for device in self.settings.get(CONF_SMART_PLUGS, []):
            serial = device.get("serial")
            if serial and "VUL_HIER" not in serial:
                await self.async_set_smart_plug(serial, plug_on)

    async def async_set_smart_plug(self, serial: str, on: bool) -> None:
        """Set a configured EcoFlow smart plug on or off."""
        device = self._smart_plug(serial)
        template = device["on_command"] if on else device["off_command"]
        command = render_template_dict(template, {"on": on})
        if self.dry_run:
            self.async_set_updated_data(
                {**(self.data or {}), "last_action": f"dry-run plug {serial} -> {on}"}
            )
            return
        await self.ecoflow.set_device_command(serial, command)
        self.async_set_updated_data(
            {**(self.data or {}), "last_action": f"plug {serial} -> {on}"}
        )

    def _powerstream(self, serial: str) -> dict[str, Any]:
        for device in self.settings.get(CONF_POWERSTREAMS, []):
            if device.get("serial") == serial:
                return device
        raise ValueError(f"Unknown PowerStream serial: {serial}")

    def _smart_plug(self, serial: str) -> dict[str, Any]:
        for device in self.settings.get(CONF_SMART_PLUGS, []):
            if device.get("serial") == serial:
                return device
        raise ValueError(f"Unknown smart plug serial: {serial}")

    def _tracked_powerstream_export(self, phase: str | None = None) -> float:
        total = 0.0
        for device in self.settings.get(CONF_POWERSTREAMS, []):
            serial = device.get("serial")
            if not serial:
                continue
            if phase and str(device.get("phase", "")).lower() != phase:
                continue
            total += float(self.powerstream_targets.get(serial, 0))
        return total


def _extract_values(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    if isinstance(data, dict):
        if isinstance(data.get("quotas"), dict):
            return data["quotas"]
        return data
    return {}
