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
from .api.prices import current_price, fetch_prices, price_bands
from .api.sma_cloud import read_sma_device
from .const import (
    CONF_ACCESS_KEY,
    CONF_BATTERIES,
    CONF_DRY_RUN,
    CONF_ECOFLOW_HOST,
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

        return {
            "price_now": price_now,
            "price_bands": bands,
            "prices": prices,
            "batteries": batteries,
            "inverters": inverters,
            "solar_power": solar_power,
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
        self.async_set_updated_data(
            {**(self.data or {}), "last_action": f"{serial} -> {watts} W"}
        )

    async def async_apply_strategy(self) -> None:
        """Apply the currently selected simple price strategy."""
        price_now = (self.data or {}).get("price_now")
        bands = (self.data or {}).get("price_bands") or {}
        if price_now is None or self.strategy == STRATEGY_IDLE:
            return

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

        solar_power = float((self.data or {}).get("solar_power") or 0)
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


def _extract_values(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    if isinstance(data, dict):
        if isinstance(data.get("quotas"), dict):
            return data["quotas"]
        return data
    return {}
