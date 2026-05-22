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
from .api.prices import current_price, fetch_prices
from .api.sma import SmaInverter, read_inverter
from .const import (
    CONF_ACCESS_KEY,
    CONF_BATTERIES,
    CONF_DRY_RUN,
    CONF_ECOFLOW_HOST,
    CONF_POWERSTREAMS,
    CONF_PRICE_URL,
    CONF_SECRET_KEY,
    CONF_SMA_INVERTERS,
    DEFAULT_ECOFLOW_HOST,
    DEFAULT_PRICE_URL,
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
        self.expensive_threshold = 0.32
        self.cheap_threshold = 0.12
        self.export_watts = 600
        self.self_use_watts = 0
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
        for item in settings.get(CONF_SMA_INVERTERS, []):
            host = item.get("host")
            if not host:
                continue
            inverter = SmaInverter(
                name=item.get("name", host),
                host=host,
                port=int(item.get("port", 502)),
                unit_id=int(item.get("unit_id", 3)),
            )
            try:
                inverters[inverter.name] = await read_inverter(inverter)
            except Exception as err:  # noqa: BLE001
                inverters[inverter.name] = {"available": False, "error": str(err)}

        return {
            "price_now": price_now,
            "prices": prices,
            "batteries": batteries,
            "inverters": inverters,
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
        if price_now is None or self.strategy == STRATEGY_IDLE:
            return

        target = self.self_use_watts
        if price_now <= self.cheap_threshold:
            target = 0
        elif price_now >= self.expensive_threshold:
            target = self.export_watts

        for device in self.settings.get(CONF_POWERSTREAMS, []):
            serial = device.get("serial")
            if serial and "VUL_HIER" not in serial:
                await self.async_set_powerstream_watts(serial, target)

    def _powerstream(self, serial: str) -> dict[str, Any]:
        for device in self.settings.get(CONF_POWERSTREAMS, []):
            if device.get("serial") == serial:
                return device
        raise ValueError(f"Unknown PowerStream serial: {serial}")


def _extract_values(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    if isinstance(data, dict):
        if isinstance(data.get("quotas"), dict):
            return data["quotas"]
        return data
    return {}

