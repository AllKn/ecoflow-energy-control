"""Config flow for EcoFlow Energy Control."""

from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_ACCESS_KEY,
    CONF_BATTERIES,
    CONF_DRY_RUN,
    CONF_ECOFLOW_HOST,
    CONF_POWERSTREAMS,
    CONF_PRICE_URL,
    CONF_SECRET_KEY,
    CONF_SMA_INVERTERS,
    DEFAULT_BATTERY_QUOTAS,
    DEFAULT_ECOFLOW_HOST,
    DEFAULT_POWERSTREAM_COMMAND,
    DEFAULT_PRICE_URL,
    DOMAIN,
)


class EcoFlowEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                _loads(user_input[CONF_BATTERIES])
                _loads(user_input[CONF_POWERSTREAMS])
                _loads(user_input[CONF_SMA_INVERTERS])
            except ValueError:
                errors["base"] = "invalid_json"
            else:
                data = dict(user_input)
                data[CONF_BATTERIES] = _loads(data[CONF_BATTERIES])
                data[CONF_POWERSTREAMS] = _loads(data[CONF_POWERSTREAMS])
                data[CONF_SMA_INVERTERS] = _loads(data[CONF_SMA_INVERTERS])
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="EcoFlow Energy Control"): str,
                vol.Required(CONF_ACCESS_KEY): str,
                vol.Required(CONF_SECRET_KEY): str,
                vol.Required(CONF_ECOFLOW_HOST, default=DEFAULT_ECOFLOW_HOST): str,
                vol.Required(CONF_PRICE_URL, default=DEFAULT_PRICE_URL): str,
                vol.Required(CONF_BATTERIES, default=_default_batteries()): str,
                vol.Required(CONF_POWERSTREAMS, default=_default_powerstreams()): str,
                vol.Required(CONF_SMA_INVERTERS, default=_default_sma()): str,
                vol.Required(CONF_DRY_RUN, default=True): bool,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return EcoFlowEnergyOptionsFlow(config_entry)


class EcoFlowEnergyOptionsFlow(config_entries.OptionsFlow):
    """Options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        current = {**self._entry.data, **self._entry.options}
        if user_input is not None:
            try:
                user_input[CONF_BATTERIES] = _loads(user_input[CONF_BATTERIES])
                user_input[CONF_POWERSTREAMS] = _loads(user_input[CONF_POWERSTREAMS])
                user_input[CONF_SMA_INVERTERS] = _loads(user_input[CONF_SMA_INVERTERS])
            except ValueError:
                errors["base"] = "invalid_json"
            else:
                return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PRICE_URL, default=current.get(CONF_PRICE_URL, DEFAULT_PRICE_URL)
                ): str,
                vol.Required(
                    CONF_BATTERIES,
                    default=json.dumps(current.get(CONF_BATTERIES, []), indent=2),
                ): str,
                vol.Required(
                    CONF_POWERSTREAMS,
                    default=json.dumps(current.get(CONF_POWERSTREAMS, []), indent=2),
                ): str,
                vol.Required(
                    CONF_SMA_INVERTERS,
                    default=json.dumps(current.get(CONF_SMA_INVERTERS, []), indent=2),
                ): str,
                vol.Required(CONF_DRY_RUN, default=current.get(CONF_DRY_RUN, True)): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


def _loads(value: str) -> Any:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as err:
        raise ValueError from err
    if not isinstance(parsed, list):
        raise ValueError
    return parsed


def _default_batteries() -> str:
    return json.dumps(
        [
            {
                "name": "Delta Pro",
                "serial": "VUL_HIER_SERIENUMMER_IN",
                "quotas": DEFAULT_BATTERY_QUOTAS,
            },
            {
                "name": "Delta Pro 3",
                "serial": "VUL_HIER_SERIENUMMER_IN",
                "quotas": DEFAULT_BATTERY_QUOTAS,
            },
        ],
        indent=2,
    )


def _default_powerstreams() -> str:
    return json.dumps(
        [
            {
                "name": "PowerStream 1",
                "serial": "VUL_HIER_SERIENUMMER_IN",
                "max_watts": 800,
                "command": DEFAULT_POWERSTREAM_COMMAND,
            },
            {
                "name": "PowerStream 2",
                "serial": "VUL_HIER_SERIENUMMER_IN",
                "max_watts": 800,
                "command": DEFAULT_POWERSTREAM_COMMAND,
            },
        ],
        indent=2,
    )


def _default_sma() -> str:
    return json.dumps(
        [
            {
                "name": "Sunny Boy 1",
                "host": "192.168.1.50",
                "port": 502,
                "unit_id": 3,
            }
        ],
        indent=2,
    )

