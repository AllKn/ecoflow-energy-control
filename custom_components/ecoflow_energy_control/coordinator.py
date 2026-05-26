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
from .api.homewizard import read_homewizard_ha_meter, read_homewizard_meter
from .api.prices import (
    current_price,
    energyzero_url,
    epexspot_url,
    epexprijzen_url,
    fetch_prices,
    price_bands,
    price_summary,
)
from .api.sma_cloud import read_sma_device
from .const import (
    CONF_ACCESS_KEY,
    CONF_BATTERIES,
    CONF_DRY_RUN,
    CONF_ECOFLOW_HOST,
    CONF_HOMEWIZARD_METERS,
    CONF_POWERSTREAMS,
    CONF_PRICE_INTERVAL,
    CONF_PRICE_INCL_VAT,
    CONF_PRICE_PROVIDER,
    CONF_PRICE_SOURCE,
    CONF_PRICE_SURCHARGE,
    CONF_PRICE_URL,
    CONF_SECRET_KEY,
    CONF_SMA_API_HOST,
    CONF_SMA_ENDPOINT,
    CONF_SMA_INVERTERS,
    CONF_SMA_PLANT_ID,
    CONF_SMA_TOKEN,
    CONF_SMART_PLUGS,
    DEFAULT_ECOFLOW_HOST,
    DEFAULT_POWERSTREAM_QUOTAS,
    DEFAULT_PRICE_INTERVAL,
    DEFAULT_PRICE_INCL_VAT,
    DEFAULT_PRICE_PROVIDER,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_PRICE_SURCHARGE,
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
        self.hass = hass
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
        self._scenario_last_update = dt_util.now()
        self._scenario_totals: dict[str, dict[str, float]] = {}
        self._scenario_periods = self._scenario_period_keys(self._scenario_last_update)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        settings = {**self.entry.data, **self.entry.options}
        errors: dict[str, str] = {}
        previous = self.data or {}

        try:
            prices = await self._async_fetch_prices(settings)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Could not fetch electricity prices: %s", err)
            errors["prices"] = str(err)
            prices = previous.get("prices", [])
        price_now = current_price(prices, dt_util.now())
        bands = price_bands(prices)
        summary = price_summary(prices, dt_util.now())

        batteries = {}
        for device in settings.get(CONF_BATTERIES, []):
            serial = device.get("serial")
            if not serial or "VUL_HIER" in serial:
                continue
            try:
                source = "selected"
                try:
                    response = await self.ecoflow.get_device_quotas(
                        serial, device.get("quotas")
                    )
                except Exception:  # noqa: BLE001
                    source = "all_after_selected_error"
                    response = await self.ecoflow.get_device_quotas(serial, None)
                values = _extract_values(response)
                if not values:
                    source = "all_after_empty_selected"
                    response = await self.ecoflow.get_device_quotas(serial, None)
                    values = _extract_values(response)
                elif _needs_battery_power_fallback(values):
                    source = "all_after_missing_power"
                    response = await self.ecoflow.get_device_quotas(serial, None)
                    all_values = _extract_values(response)
                    if all_values:
                        values = all_values
                batteries[serial] = {
                    "name": device.get("name", serial),
                    "response": response,
                    "values": values,
                    "quota_source": source,
                    "response_debug": _response_debug(response),
                }
            except Exception as err:  # noqa: BLE001
                errors[f"battery_{serial}"] = str(err)
                batteries[serial] = {"name": device.get("name", serial), "error": str(err)}

        powerstreams = {}
        for device in settings.get(CONF_POWERSTREAMS, []):
            serial = device.get("serial")
            if not serial or "VUL_HIER" in serial:
                continue
            target_watts = float(self.powerstream_targets.get(serial, 0))
            try:
                try:
                    response = await self.ecoflow.get_device_quotas(
                        serial, device.get("quotas", DEFAULT_POWERSTREAM_QUOTAS)
                    )
                except Exception:  # noqa: BLE001
                    response = await self.ecoflow.get_device_quotas(serial, None)
                values = _extract_values(response)
                if not values:
                    response = await self.ecoflow.get_device_quotas(serial, None)
                    values = _extract_values(response)
                raw_target_watts = _first_number_or_match(
                    values,
                    (
                        "permanentWatts",
                        "inv.outputWatts",
                        "invOutputWatts",
                        "invOutWatts",
                        "outputWatts",
                        "outputPower",
                        "gridOutputWatts",
                        "gridOutputPower",
                        "acOutputWatts",
                        "ac.outputWatts",
                    ),
                    target_watts,
                )
                target_watts = _normalize_powerstream_watts(
                    raw_target_watts,
                    float(device.get("max_watts") or 0),
                )
                powerstreams[serial] = {
                    "name": device.get("name", serial),
                    "response": response,
                    "values": values,
                    "target_watts": target_watts,
                    "raw_target_watts": raw_target_watts,
                    "phase": device.get("phase", "l1"),
                    "battery_serial": device.get("battery_serial"),
                    "battery_name": _battery_name(
                        settings, device.get("battery_serial")
                    ),
                    "battery_soc": _battery_soc_for_serial(
                        batteries, device.get("battery_serial")
                    ),
                    "response_debug": _response_debug(response),
                }
            except Exception as err:  # noqa: BLE001
                errors[f"powerstream_{serial}"] = str(err)
                powerstreams[serial] = {
                    "name": device.get("name", serial),
                    "values": {},
                    "target_watts": target_watts,
                    "phase": device.get("phase", "l1"),
                    "battery_serial": device.get("battery_serial"),
                    "battery_name": _battery_name(
                        settings, device.get("battery_serial")
                    ),
                    "battery_soc": _battery_soc_for_serial(
                        batteries, device.get("battery_serial")
                    ),
                    "error": str(err),
                }

        smart_plugs = {}
        for device in settings.get(CONF_SMART_PLUGS, []):
            serial = device.get("serial")
            if not serial or "VUL_HIER" in serial:
                continue
            try:
                response = await self.ecoflow.get_device_quotas(
                    serial, device.get("quotas")
                )
                smart_plugs[serial] = {
                    "name": device.get("name", serial),
                    "response": response,
                    "values": _extract_values(response),
                    "charges": device.get("charges"),
                }
            except Exception as err:  # noqa: BLE001
                errors[f"smart_plug_{serial}"] = str(err)
                smart_plugs[serial] = {
                    "name": device.get("name", serial),
                    "values": {},
                    "charges": device.get("charges"),
                    "error": str(err),
                }

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
                errors[f"sma_{device_id}"] = str(err)
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
            source_id = item.get("host") or item.get("device_id")
            if not source_id:
                continue
            try:
                if item.get("source") == "homeassistant":
                    reading = read_homewizard_ha_meter(self.hass, item)
                else:
                    reading = await read_homewizard_meter(self.session, item)
                name = item.get("name", source_id)
                homewizard_meters[name] = reading
                if reading.get("role") == "solar_total":
                    active_power = float(reading.get("active_power_w") or 0)
                    homewizard_solar_power += abs(active_power)
                    for phase, watts in reading.get("phase_power_w", {}).items():
                        homewizard_phase_power[phase] += abs(float(watts or 0))
            except Exception as err:  # noqa: BLE001
                errors[f"homewizard_{source_id}"] = str(err)
                homewizard_meters[item.get("name", source_id)] = {
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
        scenarios = self._simulate_scenarios(
            settings,
            price_now,
            bands,
            batteries,
            effective_solar_power,
        )

        return {
            "price_now": price_now,
            "price_bands": bands,
            "price_summary": summary,
            "prices": prices,
            "batteries": batteries,
            "powerstreams": powerstreams,
            "smart_plugs": smart_plugs,
            "inverters": inverters,
            "homewizard_meters": homewizard_meters,
            "solar_power": solar_power,
            "homewizard_solar_power": homewizard_solar_power,
            "powerstream_export_w": powerstream_export,
            "corrected_solar_power": effective_solar_power,
            "corrected_phase_power": corrected_phase_power,
            "scenarios": scenarios,
            "strategy": self.strategy,
            "dry_run": self.dry_run,
            "last_action": previous.get("last_action"),
            "errors": errors,
            "status": "ok" if not errors else f"{len(errors)} bron(nen) met fout",
        }

    def _simulate_scenarios(
        self,
        settings: dict[str, Any],
        price_now: float | None,
        bands: dict[str, float | None],
        batteries: dict[str, Any],
        solar_power_w: float,
    ) -> dict[str, dict[str, Any]]:
        now = dt_util.now()
        elapsed_hours = max(
            0.0, min((now - self._scenario_last_update).total_seconds() / 3600, 1.0)
        )
        self._scenario_last_update = now
        periods = self._scenario_period_keys(now)
        if periods != self._scenario_periods:
            self._reset_changed_scenario_periods(periods)
            self._scenario_periods = periods

        price = float(price_now or 0)
        cheap = bands.get("cheap")
        expensive = bands.get("expensive")
        spread = max(0.0, float(expensive or price) - float(cheap or price))
        export_capacity_w = self._configured_powerstream_capacity(settings)
        battery_soc = _battery_min_soc(batteries)
        usable_export_w = export_capacity_w if battery_soc is None or battery_soc > 10 else 0.0
        buffer_export_w = export_capacity_w if battery_soc is None or battery_soc > 50 else 0.0
        solar_surplus_w = max(0.0, float(solar_power_w or 0))

        simulated = {
            "self_use": self._scenario_result(
                label="Optimalisatie eigen gebruik",
                action="solar laden" if solar_surplus_w > 100 else "stand-by",
                power_w=min(solar_surplus_w, export_capacity_w),
                eur_per_hour=(min(solar_surplus_w, export_capacity_w) / 1000) * max(price, spread),
                price=price,
                battery_soc=battery_soc,
            ),
            "trading": self._scenario_result(
                label="Handelen",
                action="terugleveren"
                if expensive is not None and price >= expensive and usable_export_w > 0
                else "laden"
                if cheap is not None and price <= cheap
                else "wachten",
                power_w=usable_export_w
                if expensive is not None and price >= expensive
                else -min(solar_surplus_w or export_capacity_w, export_capacity_w)
                if cheap is not None and price <= cheap
                else 0.0,
                eur_per_hour=(usable_export_w / 1000) * price
                if expensive is not None and price >= expensive
                else -(min(solar_surplus_w or export_capacity_w, export_capacity_w) / 1000) * price
                if cheap is not None and price <= cheap
                else 0.0,
                price=price,
                battery_soc=battery_soc,
            ),
            "buffer_50": self._scenario_result(
                label="Buffer 50%",
                action="terugleveren boven buffer"
                if buffer_export_w > 0 and expensive is not None and price >= expensive
                else "buffer bewaken",
                power_w=buffer_export_w if expensive is not None and price >= expensive else 0.0,
                eur_per_hour=(buffer_export_w / 1000) * price
                if expensive is not None and price >= expensive
                else 0.0,
                price=price,
                battery_soc=battery_soc,
            ),
        }

        for key, item in simulated.items():
            totals = self._scenario_totals.setdefault(
                key, {"day": 0.0, "week": 0.0, "month": 0.0}
            )
            delta = float(item["eur_per_hour"]) * elapsed_hours
            totals["day"] += delta
            totals["week"] += delta
            totals["month"] += delta
            item["day_eur"] = round(totals["day"], 4)
            item["week_eur"] = round(totals["week"], 4)
            item["month_eur"] = round(totals["month"], 4)
        return simulated

    def _scenario_result(
        self,
        label: str,
        action: str,
        power_w: float,
        eur_per_hour: float,
        price: float,
        battery_soc: float | None,
    ) -> dict[str, Any]:
        return {
            "label": label,
            "action": action,
            "power_w": round(power_w, 1),
            "eur_per_hour": round(eur_per_hour, 4),
            "price_eur_kwh": price,
            "battery_soc": battery_soc,
        }

    def _scenario_period_keys(self, now) -> dict[str, str]:
        return {
            "day": now.strftime("%Y-%m-%d"),
            "week": f"{now.isocalendar().year}-W{now.isocalendar().week:02d}",
            "month": now.strftime("%Y-%m"),
        }

    def _reset_changed_scenario_periods(self, periods: dict[str, str]) -> None:
        for key, totals in self._scenario_totals.items():
            for period, value in periods.items():
                if self._scenario_periods.get(period) != value:
                    totals[period] = 0.0

    def _configured_powerstream_capacity(self, settings: dict[str, Any]) -> float:
        capacity = 0.0
        for device in settings.get(CONF_POWERSTREAMS, []):
            try:
                capacity += float(device.get("max_watts") or 0)
            except (TypeError, ValueError):
                continue
        return capacity or float(self.export_watts or 0)

    async def async_set_powerstream_watts(self, serial: str, watts: int) -> None:
        """Set a PowerStream output target using configured command template."""
        device = self._powerstream(serial)
        watts = max(0, min(watts, int(device.get("max_watts", watts))))
        command = render_template_dict(device["command"], {"watts": watts})
        self.powerstream_targets[serial] = watts
        if self.dry_run:
            self.async_set_updated_data(
                {**(self.data or {}), "last_action": f"dry-run {serial} -> {watts} W"}
            )
            return
        await self.ecoflow.set_device_command(serial, command)
        self.async_set_updated_data(
            {**(self.data or {}), "last_action": f"{serial} -> {watts} W"}
        )

    async def async_check_ecoflow_api(self) -> None:
        """Manually validate EcoFlow API credentials and device-list access."""
        data = dict(self.data or {})
        errors = dict(data.get("errors") or {})
        try:
            response = await self.ecoflow.get_devices()
            serials = _extract_serials(response)
        except Exception as err:  # noqa: BLE001
            errors["ecoflow_api"] = str(err)
            data.update(
                {
                    "errors": errors,
                    "status": "EcoFlow API fout",
                    "last_action": f"EcoFlow API controle mislukt: {err}",
                }
            )
        else:
            errors.pop("ecoflow_api", None)
            data.update(
                {
                    "ecoflow_devices": serials,
                    "errors": errors,
                    "status": "ok" if not errors else f"{len(errors)} bron(nen) met fout",
                    "last_action": f"EcoFlow API ok, {len(serials)} apparaat/apparaten gevonden",
                }
            )
        self.async_set_updated_data(data)

    async def async_refresh_prices_now(self) -> None:
        """Manually fetch day-ahead prices."""
        data = dict(self.data or {})
        errors = dict(data.get("errors") or {})
        settings = {**self.entry.data, **self.entry.options}
        try:
            prices = await self._async_fetch_prices(settings)
        except Exception as err:  # noqa: BLE001
            errors["prices"] = str(err)
            data.update(
                {
                    "errors": errors,
                    "status": "prijsfeed fout",
                    "last_action": f"Prijzen ophalen mislukt: {err}",
                }
            )
        else:
            errors.pop("prices", None)
            data.update(
                {
                    "prices": prices,
                    "price_now": current_price(prices, dt_util.now()),
                    "price_bands": price_bands(prices),
                    "price_summary": price_summary(prices, dt_util.now()),
                    "errors": errors,
                    "status": "ok" if not errors else f"{len(errors)} bron(nen) met fout",
                    "last_action": f"Prijzen opgehaald, {len(prices)} uurrecords",
                }
            )
        self.async_set_updated_data(data)

    async def async_daily_price_refresh(self) -> None:
        """Fetch prices for the next day at the scheduled 15:00 refresh."""
        await self.async_refresh_prices_now()

    async def _async_fetch_prices(self, settings: dict[str, Any]) -> list[dict[str, Any]]:
        source = settings.get(CONF_PRICE_SOURCE, DEFAULT_PRICE_SOURCE)
        provider = settings.get(CONF_PRICE_PROVIDER, DEFAULT_PRICE_PROVIDER)
        interval = settings.get(CONF_PRICE_INTERVAL, DEFAULT_PRICE_INTERVAL)
        surcharge = float(settings.get(CONF_PRICE_SURCHARGE, DEFAULT_PRICE_SURCHARGE))
        if settings.get(CONF_PRICE_URL):
            return await fetch_prices(self.session, settings[CONF_PRICE_URL], surcharge)
        today = dt_util.now().date()
        if source == "energyzero":
            incl_vat = bool(settings.get(CONF_PRICE_INCL_VAT, DEFAULT_PRICE_INCL_VAT))
            record_keys = ("base_with_vat", "base") if incl_vat else ("base", "base_with_vat")
            prices: list[dict[str, Any]] = []
            for day in (today, today + timedelta(days=1)):
                prices.extend(
                    await fetch_prices(
                        self.session,
                        energyzero_url(day, interval),
                        surcharge,
                        record_keys,
                    )
                )
            return prices
        if source == "epexspot":
            prices: list[dict[str, Any]] = []
            for day in (today, today + timedelta(days=1)):
                prices.extend(await fetch_prices(self.session, epexspot_url(day), surcharge))
            return prices
        return await fetch_prices(self.session, epexprijzen_url(provider, interval), surcharge)

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
        if isinstance(data.get("quotas"), list):
            return _quota_list_to_values(data["quotas"])
        if isinstance(data.get("quotas"), dict):
            return _flatten_value_dict(data["quotas"])
        return _flatten_value_dict(data)
    if isinstance(data, list):
        return _quota_list_to_values(data)
    return {}


def _response_debug(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    return {
        "code": response.get("code"),
        "message": response.get("message"),
        "top_level_keys": sorted(response.keys()),
        "data_type": type(data).__name__,
        "data_keys": sorted(data.keys())[:40] if isinstance(data, dict) else [],
        "data_length": len(data) if isinstance(data, list) else None,
    }


def _quota_list_to_values(records: list[Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for item in records:
        if not isinstance(item, dict):
            continue
        key = _first_text(item, ("name", "key", "quota", "param", "code", "id"))
        if not key:
            continue
        if "value" in item:
            values[key] = item["value"]
        elif "val" in item:
            values[key] = item["val"]
        elif "data" in item:
            values[key] = item["data"]
    return values


def _flatten_value_dict(data: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    _flatten_values(data, "", values)
    return values


def _flatten_values(data: Any, prefix: str, values: dict[str, Any]) -> None:
    if isinstance(data, dict):
        if "value" in data and prefix:
            values[prefix] = data["value"]
            return
        for key, value in data.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            _flatten_values(value, child_key, values)
        return
    if isinstance(data, list):
        quota_values = _quota_list_to_values(data)
        if quota_values:
            for key, value in quota_values.items():
                values[f"{prefix}.{key}" if prefix else key] = value
            return
        for index, value in enumerate(data):
            child_key = f"{prefix}[{index}]" if prefix else f"[{index}]"
            _flatten_values(value, child_key, values)
        return
    if prefix:
        values[prefix] = data


def _first_number_or_match(
    values: dict[str, Any], keys: tuple[str, ...], default: float = 0.0
) -> float:
    exact = _first_number(values, keys, None)
    if exact is not None:
        return exact
    for key, value in values.items():
        normalized = key.lower().replace("_", "").replace("-", "")
        if "watt" not in normalized and "power" not in normalized:
            continue
        if "input" in normalized or "pv" in normalized or "solar" in normalized:
            continue
        if not any(part in normalized for part in ("output", "out", "grid", "inv", "permanent", "ac")):
            continue
        if isinstance(value, dict) and "value" in value:
            value = value["value"]
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _needs_battery_power_fallback(values: dict[str, Any]) -> bool:
    power_fields = _battery_live_power_fields(values)
    if not power_fields:
        return True
    if len(values) <= 3 and not any(abs(value) > 0 for value in power_fields):
        return True
    if not _has_directional_power_field(values, "charge"):
        return True
    if not _has_directional_power_field(values, "discharge"):
        return True
    return False


def _battery_live_power_fields(values: dict[str, Any]) -> list[float]:
    fields: list[float] = []
    for key, value in values.items():
        normalized = key.lower().replace("_", "").replace("-", "").replace(".", "")
        if not _is_battery_live_power_key(normalized):
            continue
        numeric = _coerce_float(value)
        if numeric is not None:
            fields.append(numeric)
    return fields


def _has_directional_power_field(values: dict[str, Any], direction: str) -> bool:
    parts = (
        ("input", "charge", "chg", "powin", "wattsin", "acin", "dcin", "pvin")
        if direction == "charge"
        else ("output", "discharge", "dsg", "powout", "wattsout", "acout", "dcout", "invout")
    )
    for key, value in values.items():
        normalized = key.lower().replace("_", "").replace("-", "").replace(".", "")
        if not _is_battery_live_power_key(normalized):
            continue
        if not any(part in normalized for part in parts):
            continue
        if _coerce_float(value) is not None:
            return True
    return False


def _is_battery_live_power_key(normalized: str) -> bool:
    if not any(part in normalized for part in ("watt", "power", "pow")):
        return False
    return not any(
        part in normalized
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


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, dict) and "value" in value:
        value = value["value"]
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _first_number(
    values: dict[str, Any], keys: tuple[str, ...], default: float | None = 0.0
) -> float | None:
    for key in keys:
        value = values.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _first_text(values: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = values.get(key)
        if value is not None:
            return str(value)
    return None


def _battery_min_soc(batteries: dict[str, Any]) -> float | None:
    values: list[float] = []
    for item in batteries.values():
        battery_values = item.get("values", {}) if isinstance(item, dict) else {}
        soc = _battery_soc_value(battery_values)
        if soc is not None:
            values.append(float(soc))
    if not values:
        return None
    return min(values)


def _battery_soc_for_serial(
    batteries: dict[str, Any], serial: str | None
) -> float | None:
    if not serial:
        return None
    item = batteries.get(str(serial)) or {}
    return _battery_soc_value(item.get("values", {}))


def _battery_name(settings: dict[str, Any], serial: str | None) -> str | None:
    if not serial:
        return None
    for device in settings.get(CONF_BATTERIES, []):
        if str(device.get("serial")) == str(serial):
            return str(device.get("name") or serial)
    return str(serial)


def _battery_soc_value(values: dict[str, Any]) -> float | None:
    soc = _first_number(
        values,
        (
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
        ),
        None,
    )
    if soc is not None:
        return max(0.0, min(float(soc), 100.0))
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


def _is_soc_limit_or_setting(normalized_key: str) -> bool:
    blocked_parts = (
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
    return any(part in normalized_key for part in blocked_parts)


def _normalize_powerstream_watts(value: float | None, max_watts: float) -> float:
    if value is None:
        return 0.0
    normalized = float(value)
    if max_watts > 0 and abs(normalized) > max_watts * 1.5:
        if abs(normalized / 10) <= max_watts * 1.5:
            normalized = normalized / 10
    elif abs(normalized) > 1000 and abs(normalized / 10) <= 1000:
        normalized = normalized / 10
    return round(normalized, 1)


def _extract_serials(response: dict[str, Any]) -> list[str]:
    serials: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"sn", "serial", "serialNumber", "deviceSn"} and item:
                    serials.add(str(item))
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(response.get("data", response))
    return sorted(serials)
