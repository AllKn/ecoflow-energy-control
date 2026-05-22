"""Config flow for EcoFlow Energy Control."""

from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.ecoflow import EcoFlowCloudClient
from .api.homewizard import read_homewizard_meter
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
    DEFAULT_BATTERY_QUOTAS,
    DEFAULT_ECOFLOW_HOST,
    DEFAULT_HOMEWIZARD_ROLE,
    DEFAULT_POWERSTREAM_COMMAND,
    DEFAULT_PRICE_URL,
    DEFAULT_SMA_API_HOST,
    DEFAULT_SMA_ENDPOINT,
    DEFAULT_SMART_PLUG_OFF_COMMAND,
    DEFAULT_SMART_PLUG_ON_COMMAND,
    DOMAIN,
)


class EcoFlowEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial setup."""

    VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            data = {
                **user_input,
                CONF_BATTERIES: [],
                CONF_POWERSTREAMS: [],
                CONF_SMA_INVERTERS: [],
                CONF_SMART_PLUGS: [],
                CONF_HOMEWIZARD_METERS: [],
            }
            return self.async_create_entry(title=user_input[CONF_NAME], data=data)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, default="EcoFlow Energy Control Applicatie"
                ): str,
                vol.Required(CONF_ACCESS_KEY): str,
                vol.Required(CONF_SECRET_KEY): str,
                vol.Required(CONF_ECOFLOW_HOST, default=DEFAULT_ECOFLOW_HOST): str,
                vol.Required(CONF_PRICE_URL, default=DEFAULT_PRICE_URL): str,
                vol.Optional(CONF_SMA_API_HOST, default=DEFAULT_SMA_API_HOST): str,
                vol.Optional(CONF_SMA_TOKEN, default=""): str,
                vol.Optional(CONF_SMA_PLANT_ID, default=""): str,
                vol.Optional(CONF_SMA_ENDPOINT, default=DEFAULT_SMA_ENDPOINT): str,
                vol.Required(CONF_DRY_RUN, default=True): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return EcoFlowEnergyOptionsFlow(config_entry)


class EcoFlowEnergyOptionsFlow(config_entries.OptionsFlow):
    """Options flow with one-device-at-a-time editing."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._pending_remove: str | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "general",
                "add_device",
                "remove_device",
            ],
        )

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            return await getattr(self, f"async_step_device_{user_input['device_type']}")()
        return self.async_show_form(
            step_id="add_device",
            data_schema=vol.Schema(
                {
                    vol.Required("device_type"): vol.In(
                        {
                            "delta_pro": "EcoFlow Delta Pro",
                            "delta_pro_3": "EcoFlow Delta Pro 3",
                            "powerstream": "EcoFlow PowerStream",
                            "smart_plug": "EcoFlow Smart Plug",
                            "homewizard": "HomeWizard lokale meter",
                            "sma": "SMA cloud omvormer",
                        }
                    )
                }
            ),
        )

    async def async_step_general(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        current = self._settings()
        if user_input is not None:
            return self._save(user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PRICE_URL, default=current.get(CONF_PRICE_URL, DEFAULT_PRICE_URL)
                ): str,
                vol.Optional(
                    CONF_SMA_API_HOST,
                    default=current.get(CONF_SMA_API_HOST, DEFAULT_SMA_API_HOST),
                ): str,
                vol.Optional(CONF_SMA_TOKEN, default=current.get(CONF_SMA_TOKEN, "")): str,
                vol.Optional(
                    CONF_SMA_PLANT_ID, default=current.get(CONF_SMA_PLANT_ID, "")
                ): str,
                vol.Optional(
                    CONF_SMA_ENDPOINT,
                    default=current.get(CONF_SMA_ENDPOINT, DEFAULT_SMA_ENDPOINT),
                ): str,
                vol.Required(CONF_DRY_RUN, default=current.get(CONF_DRY_RUN, True)): bool,
            }
        )
        return self.async_show_form(step_id="general", data_schema=schema)

    async def async_step_add_battery(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self.async_step_device_delta_pro(user_input)

    async def async_step_device_delta_pro(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self._async_battery_form("device_delta_pro", "Delta Pro", user_input)

    async def async_step_device_delta_pro_3(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self._async_battery_form(
            "device_delta_pro_3", "Delta Pro 3", user_input
        )

    async def _async_battery_form(
        self, step_id: str, default_name: str, user_input: dict[str, Any] | None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._validate_ecoflow_device(
                    user_input["serial"], DEFAULT_BATTERY_QUOTAS
                )
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                values = self._settings()
                values.setdefault(CONF_BATTERIES, []).append(
                    {
                        "name": user_input["name"],
                        "model": default_name,
                        "serial": user_input["serial"],
                        "quotas": DEFAULT_BATTERY_QUOTAS,
                    }
                )
                return self._save(values)
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=default_name): str,
                    vol.Required("serial"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_add_powerstream(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self.async_step_device_powerstream(user_input)

    async def async_step_device_powerstream(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                command = json.loads(user_input["command"])
            except json.JSONDecodeError:
                errors["command"] = "invalid_json"
            else:
                try:
                    await self._validate_ecoflow_device(user_input["serial"], None)
                except Exception:  # noqa: BLE001
                    errors["base"] = "cannot_connect"
                else:
                    values = self._settings()
                    values.setdefault(CONF_POWERSTREAMS, []).append(
                        {
                            "name": user_input["name"],
                            "serial": user_input["serial"],
                            "max_watts": user_input["max_watts"],
                            "phase": user_input["phase"],
                            "command": command,
                        }
                    )
                    return self._save(values)
        return self.async_show_form(
            step_id="device_powerstream",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="PowerStream"): str,
                    vol.Required("serial"): str,
                    vol.Required("max_watts", default=800): int,
                    vol.Required("phase", default="l1"): vol.In(
                        {"l1": "Fase 1", "l2": "Fase 2", "l3": "Fase 3"}
                    ),
                    vol.Required(
                        "command", default=json.dumps(DEFAULT_POWERSTREAM_COMMAND)
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_add_sma(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self.async_step_device_sma(user_input)

    async def async_step_device_sma(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._validate_sma_device(dict(user_input))
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                values = self._settings()
                values.setdefault(CONF_SMA_INVERTERS, []).append(dict(user_input))
                return self._save(values)
        return self.async_show_form(
            step_id="device_sma",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="Sunny Boy"): str,
                    vol.Required("device_id"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_add_homewizard(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self.async_step_device_homewizard(user_input)

    async def async_step_device_homewizard(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await read_homewizard_meter(
                    async_get_clientsession(self.hass), dict(user_input)
                )
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                values = self._settings()
                values.setdefault(CONF_HOMEWIZARD_METERS, []).append(dict(user_input))
                return self._save(values)
        return self.async_show_form(
            step_id="device_homewizard",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="HomeWizard zonmeter"): str,
                    vol.Required("host"): str,
                    vol.Required("role", default=DEFAULT_HOMEWIZARD_ROLE): vol.In(
                        {"solar_total": "Totale opwekking"}
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_smart_plug(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self.async_step_device_smart_plug(user_input)

    async def async_step_device_smart_plug(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                on_command = json.loads(user_input["on_command"])
                off_command = json.loads(user_input["off_command"])
            except json.JSONDecodeError:
                errors["base"] = "invalid_json"
            else:
                try:
                    await self._validate_ecoflow_device(user_input["serial"], None)
                except Exception:  # noqa: BLE001
                    errors["base"] = "cannot_connect"
                else:
                    values = self._settings()
                    values.setdefault(CONF_SMART_PLUGS, []).append(
                        {
                            "name": user_input["name"],
                            "serial": user_input["serial"],
                            "charges": user_input["charges"],
                            "on_command": on_command,
                            "off_command": off_command,
                        }
                    )
                    return self._save(values)
        return self.async_show_form(
            step_id="device_smart_plug",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="Delta Pro laadstekker"): str,
                    vol.Required("serial"): str,
                    vol.Required("charges", default="Delta Pro"): str,
                    vol.Required(
                        "on_command", default=json.dumps(DEFAULT_SMART_PLUG_ON_COMMAND)
                    ): str,
                    vol.Required(
                        "off_command", default=json.dumps(DEFAULT_SMART_PLUG_OFF_COMMAND)
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_remove_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        choices = self._device_choices()
        if user_input is not None:
            values = self._settings()
            group, index_text = user_input["device"].split(":", 1)
            values[group].pop(int(index_text))
            return self._save(values)
        if not choices:
            return self.async_abort(reason="no_devices")
        return self.async_show_form(
            step_id="remove_device",
            data_schema=vol.Schema({vol.Required("device"): vol.In(choices)}),
        )

    def _settings(self) -> dict[str, Any]:
        values = {**self._entry.data, **self._entry.options}
        values.setdefault(CONF_BATTERIES, [])
        values.setdefault(CONF_POWERSTREAMS, [])
        values.setdefault(CONF_SMA_INVERTERS, [])
        values.setdefault(CONF_SMART_PLUGS, [])
        values.setdefault(CONF_HOMEWIZARD_METERS, [])
        return values

    def _save(self, values: dict[str, Any]) -> config_entries.FlowResult:
        merged = self._settings()
        merged.update(values)
        return self.async_create_entry(title="", data=merged)

    def _device_choices(self) -> dict[str, str]:
        values = self._settings()
        choices: dict[str, str] = {}
        for group, label in (
            (CONF_BATTERIES, "Batterij"),
            (CONF_POWERSTREAMS, "PowerStream"),
            (CONF_SMA_INVERTERS, "SMA"),
            (CONF_HOMEWIZARD_METERS, "HomeWizard"),
            (CONF_SMART_PLUGS, "Smart Plug"),
        ):
            for index, item in enumerate(values.get(group, [])):
                choices[f"{group}:{index}"] = f"{label}: {item.get('name', index)}"
        return choices

    async def _validate_ecoflow_device(
        self, serial: str, quotas: list[str] | None
    ) -> None:
        settings = self._settings()
        client = EcoFlowCloudClient(
            async_get_clientsession(self.hass),
            settings[CONF_ECOFLOW_HOST],
            settings[CONF_ACCESS_KEY],
            settings[CONF_SECRET_KEY],
        )
        await client.get_device_quotas(serial, quotas)

    async def _validate_sma_device(self, device: dict[str, Any]) -> None:
        settings = self._settings()
        await read_sma_device(
            async_get_clientsession(self.hass),
            settings[CONF_SMA_API_HOST],
            settings[CONF_SMA_TOKEN],
            settings[CONF_SMA_PLANT_ID],
            device,
            settings[CONF_SMA_ENDPOINT],
        )
