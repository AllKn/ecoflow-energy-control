"""Config flow for EcoFlow Energy Control."""

from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import device_registry as dr, entity_registry as er

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
    DEFAULT_BATTERY_QUOTAS,
    DEFAULT_ECOFLOW_HOST,
    DEFAULT_HOMEWIZARD_ROLE,
    DEFAULT_POWERSTREAM_COMMAND,
    DEFAULT_PRICE_INTERVAL,
    DEFAULT_PRICE_INCL_VAT,
    DEFAULT_PRICE_PROVIDER,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_PRICE_SURCHARGE,
    DEFAULT_SMA_API_HOST,
    DEFAULT_SMA_ENDPOINT,
    DEFAULT_SMART_PLUG_OFF_COMMAND,
    DEFAULT_SMART_PLUG_ON_COMMAND,
    DOMAIN,
    APP_NAME,
)

_LOGGER = logging.getLogger(__name__)


class EcoFlowEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial setup."""

    VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._validate_ecoflow_credentials(user_input)
            except Exception:  # noqa: BLE001
                errors["base"] = "ecoflow_auth_failed"
            else:
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
                    CONF_NAME, default=APP_NAME
                ): str,
                vol.Required(CONF_ACCESS_KEY): str,
                vol.Required(CONF_SECRET_KEY): str,
                vol.Required(CONF_ECOFLOW_HOST, default=DEFAULT_ECOFLOW_HOST): str,
                vol.Optional(CONF_PRICE_SOURCE, default=DEFAULT_PRICE_SOURCE): vol.In(
                    {
                        "energyzero": "EnergyZero",
                        "epexprijzen": "epexprijzen.nl",
                        "epexspot": "epexspot.com",
                    }
                ),
                vol.Optional(CONF_PRICE_PROVIDER, default=DEFAULT_PRICE_PROVIDER): str,
                vol.Optional(CONF_PRICE_INTERVAL, default=DEFAULT_PRICE_INTERVAL): vol.In(
                    {"hourly": "Uurprijzen", "quarterly": "Kwartierprijzen"}
                ),
                vol.Optional(CONF_PRICE_SURCHARGE, default=DEFAULT_PRICE_SURCHARGE): float,
                vol.Optional(CONF_PRICE_INCL_VAT, default=DEFAULT_PRICE_INCL_VAT): bool,
                vol.Optional(CONF_PRICE_URL, default=""): str,
                vol.Optional(CONF_SMA_API_HOST, default=DEFAULT_SMA_API_HOST): str,
                vol.Optional(CONF_SMA_TOKEN, default=""): str,
                vol.Optional(CONF_SMA_PLANT_ID, default=""): str,
                vol.Optional(CONF_SMA_ENDPOINT, default=DEFAULT_SMA_ENDPOINT): str,
                vol.Required(CONF_DRY_RUN, default=True): bool,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def _validate_ecoflow_credentials(self, values: dict[str, Any]) -> None:
        from .api.ecoflow import EcoFlowCloudClient

        client = EcoFlowCloudClient(
            async_get_clientsession(self.hass),
            values[CONF_ECOFLOW_HOST],
            values[CONF_ACCESS_KEY],
            values[CONF_SECRET_KEY],
        )
        await client.get_devices()

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
        self._pending_edit: tuple[str, int] | None = None
        self._pending_import_device: dict[str, Any] | None = None
        self._pending_import_config: dict[str, Any] | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "general",
                "add_device",
                "import_ecoflow",
                "import_homewizard",
                "edit_device",
                "remove_device",
            ],
        )

    async def async_step_import_homewizard(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        try:
            devices = self._homewizard_ha_devices()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Could not inspect HomeWizard devices from Home Assistant")
            devices = {}
            errors = {"base": "cannot_connect"}
        else:
            errors = {}
        choices = {
            device_id: device["label"]
            for device_id, device in devices.items()
            if not self._homewizard_ha_configured(device_id)
        }
        if user_input is not None and choices:
            selected = devices[user_input["device_id"]]
            values = self._settings()
            values.setdefault(CONF_HOMEWIZARD_METERS, []).append(
                {
                    "name": selected["name"],
                    "source": "homeassistant",
                    "device_id": user_input["device_id"],
                    "role": user_input["role"],
                    "model": selected.get("model"),
                    "entities": selected["entities"],
                }
            )
            return self._save(values)
        if not choices:
            errors["base"] = "no_importable_devices"
        return self.async_show_form(
            step_id="import_homewizard",
            data_schema=vol.Schema(
                {
                    vol.Required("device_id"): vol.In(
                        choices or {"": "Geen nieuwe HomeWizard apparaten gevonden"}
                    ),
                    vol.Required("role", default=DEFAULT_HOMEWIZARD_ROLE): vol.In(
                        {"solar_total": "Totale opwekking"}
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_import_ecoflow(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        devices: list[dict[str, Any]] = []
        try:
            devices = await self._fetch_ecoflow_devices()
        except Exception:  # noqa: BLE001
            errors["base"] = "ecoflow_auth_failed"

        choices = self._import_device_choices(devices)
        if user_input is not None and choices:
            self._pending_import_device = next(
                item for item in devices if _ecoflow_serial(item) == user_input["serial"]
            )
            return await self.async_step_import_ecoflow_configure()

        if not choices and not errors:
            errors["base"] = "no_importable_devices"

        return self.async_show_form(
            step_id="import_ecoflow",
            data_schema=vol.Schema({vol.Required("serial"): vol.In(choices)}),
            errors=errors,
        )

    async def async_step_import_ecoflow_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if self._pending_import_device is None:
            return await self.async_step_import_ecoflow()

        serial = _ecoflow_serial(self._pending_import_device)
        default_name = _ecoflow_name(self._pending_import_device)
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._validate_ecoflow_device(serial)
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                self._pending_import_config = {
                    "name": user_input["name"],
                    "device_type": user_input["device_type"],
                    "serial": serial,
                }
                if user_input["device_type"] == "powerstream":
                    return await self.async_step_import_ecoflow_powerstream()
                if user_input["device_type"] == "smart_plug":
                    return await self.async_step_import_ecoflow_smart_plug()
                return self._save_imported_ecoflow_device()

        return self.async_show_form(
            step_id="import_ecoflow_configure",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=default_name): str,
                    vol.Required("device_type"): vol.In(
                        {
                            "delta_pro": "EcoFlow Delta Pro",
                            "delta_pro_3": "EcoFlow Delta Pro 3",
                            "powerstream": "EcoFlow PowerStream",
                            "smart_plug": "EcoFlow Smart Plug",
                        }
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "serial": serial,
                "raw_type": str(
                    self._pending_import_device.get("deviceType")
                    or self._pending_import_device.get("productName")
                    or self._pending_import_device.get("model")
                    or "onbekend"
                ),
            },
        )

    async def async_step_import_ecoflow_powerstream(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if self._pending_import_config is None:
            return await self.async_step_import_ecoflow()
        if user_input is not None:
            self._pending_import_config.update(user_input)
            return self._save_imported_ecoflow_device()
        return self.async_show_form(
            step_id="import_ecoflow_powerstream",
            data_schema=vol.Schema(
                {
                    vol.Required("max_watts", default=800): int,
                    vol.Required("phase", default="l1"): vol.In(
                        {"l1": "Fase 1", "l2": "Fase 2", "l3": "Fase 3"}
                    ),
                }
            ),
        )

    async def async_step_import_ecoflow_smart_plug(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if self._pending_import_config is None:
            return await self.async_step_import_ecoflow()
        batteries = self._battery_choices()
        if user_input is not None:
            self._pending_import_config.update(user_input)
            return self._save_imported_ecoflow_device()
        return self.async_show_form(
            step_id="import_ecoflow_smart_plug",
            data_schema=vol.Schema(
                {
                    vol.Required("charges"): vol.In(
                        batteries or {"": "Geen batterij toegevoegd"}
                    )
                }
            ),
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
                            "homewizard_ha": "HomeWizard via Home Assistant",
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
        errors: dict[str, str] = {}
        if user_input is not None:
            merged = self._settings()
            merged.update(user_input)
            try:
                await self._validate_ecoflow_credentials(merged)
            except Exception:  # noqa: BLE001
                errors["base"] = "ecoflow_auth_failed"
            else:
                return self._save(user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PRICE_SOURCE,
                    default=current.get(CONF_PRICE_SOURCE, DEFAULT_PRICE_SOURCE),
                ): vol.In(
                    {
                        "energyzero": "EnergyZero",
                        "epexprijzen": "epexprijzen.nl",
                        "epexspot": "epexspot.com",
                    }
                ),
                vol.Required(
                    CONF_PRICE_PROVIDER,
                    default=current.get(CONF_PRICE_PROVIDER, DEFAULT_PRICE_PROVIDER),
                ): str,
                vol.Required(
                    CONF_PRICE_INTERVAL,
                    default=current.get(CONF_PRICE_INTERVAL, DEFAULT_PRICE_INTERVAL),
                ): vol.In({"hourly": "Uurprijzen", "quarterly": "Kwartierprijzen"}),
                vol.Required(
                    CONF_PRICE_SURCHARGE,
                    default=current.get(CONF_PRICE_SURCHARGE, DEFAULT_PRICE_SURCHARGE),
                ): float,
                vol.Required(
                    CONF_PRICE_INCL_VAT,
                    default=current.get(CONF_PRICE_INCL_VAT, DEFAULT_PRICE_INCL_VAT),
                ): bool,
                vol.Optional(
                    CONF_PRICE_URL, default=current.get(CONF_PRICE_URL, "")
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
        return self.async_show_form(
            step_id="general", data_schema=schema, errors=errors
        )

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
                await self._validate_ecoflow_device(user_input["serial"])
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
                    await self._validate_ecoflow_device(user_input["serial"])
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
                from .api.homewizard import read_homewizard_meter

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

    async def async_step_add_homewizard_ha(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self.async_step_import_homewizard(user_input)

    async def async_step_device_homewizard_ha(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self.async_step_import_homewizard(user_input)

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
                    await self._validate_ecoflow_device(user_input["serial"])
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
                    vol.Required("charges"): vol.In(
                        self._battery_choices() or {"": "Geen batterij toegevoegd"}
                    ),
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

    async def async_step_edit_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        choices = self._device_choices()
        if user_input is not None:
            group, index_text = user_input["device"].split(":", 1)
            self._pending_edit = (group, int(index_text))
            return await getattr(self, f"async_step_edit_{group}")()
        if not choices:
            return self.async_abort(reason="no_devices")
        return self.async_show_form(
            step_id="edit_device",
            data_schema=vol.Schema({vol.Required("device"): vol.In(choices)}),
        )

    async def async_step_edit_batteries(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        group, index, current = self._edit_context(CONF_BATTERIES)
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._validate_ecoflow_device(user_input["serial"])
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                item = {
                    **current,
                    "name": user_input["name"],
                    "model": user_input["model"],
                    "serial": user_input["serial"],
                    "quotas": DEFAULT_BATTERY_QUOTAS,
                }
                return self._replace_device(group, index, item)
        return self.async_show_form(
            step_id="edit_batteries",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=current.get("name", "Delta Pro")): str,
                    vol.Required(
                        "model", default=current.get("model", "Delta Pro")
                    ): vol.In({"Delta Pro": "Delta Pro", "Delta Pro 3": "Delta Pro 3"}),
                    vol.Required("serial", default=current.get("serial", "")): str,
                }
            ),
            errors=errors,
        )

    async def async_step_edit_powerstreams(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        group, index, current = self._edit_context(CONF_POWERSTREAMS)
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                command = json.loads(user_input["command"])
            except json.JSONDecodeError:
                errors["command"] = "invalid_json"
            else:
                try:
                    await self._validate_ecoflow_device(user_input["serial"])
                except Exception:  # noqa: BLE001
                    errors["base"] = "cannot_connect"
                else:
                    item = {
                        **current,
                        "name": user_input["name"],
                        "serial": user_input["serial"],
                        "max_watts": user_input["max_watts"],
                        "phase": user_input["phase"],
                        "command": command,
                    }
                    return self._replace_device(group, index, item)
        return self.async_show_form(
            step_id="edit_powerstreams",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=current.get("name", "PowerStream")): str,
                    vol.Required("serial", default=current.get("serial", "")): str,
                    vol.Required("max_watts", default=current.get("max_watts", 800)): int,
                    vol.Required("phase", default=current.get("phase", "l1")): vol.In(
                        {"l1": "Fase 1", "l2": "Fase 2", "l3": "Fase 3"}
                    ),
                    vol.Required(
                        "command",
                        default=json.dumps(
                            current.get("command", DEFAULT_POWERSTREAM_COMMAND)
                        ),
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_edit_sma_inverters(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        group, index, current = self._edit_context(CONF_SMA_INVERTERS)
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._validate_sma_device(dict(user_input))
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self._replace_device(group, index, dict(user_input))
        return self.async_show_form(
            step_id="edit_sma_inverters",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=current.get("name", "Sunny Boy")): str,
                    vol.Required("device_id", default=current.get("device_id", "")): str,
                }
            ),
            errors=errors,
        )

    async def async_step_edit_homewizard_meters(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        group, index, current = self._edit_context(CONF_HOMEWIZARD_METERS)
        if current.get("source") == "homeassistant":
            if user_input is not None:
                updated = {
                    **current,
                    "name": user_input["name"],
                    "role": user_input["role"],
                }
                return self._replace_device(group, index, updated)
            return self.async_show_form(
                step_id="edit_homewizard_meters",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            "name", default=current.get("name", "HomeWizard")
                        ): str,
                        vol.Required(
                            "role", default=current.get("role", DEFAULT_HOMEWIZARD_ROLE)
                        ): vol.In({"solar_total": "Totale opwekking"}),
                    }
                ),
            )
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                from .api.homewizard import read_homewizard_meter

                await read_homewizard_meter(
                    async_get_clientsession(self.hass), dict(user_input)
                )
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self._replace_device(group, index, dict(user_input))
        return self.async_show_form(
            step_id="edit_homewizard_meters",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "name", default=current.get("name", "HomeWizard zonmeter")
                    ): str,
                    vol.Required("host", default=current.get("host", "")): str,
                    vol.Required(
                        "role", default=current.get("role", DEFAULT_HOMEWIZARD_ROLE)
                    ): vol.In({"solar_total": "Totale opwekking"}),
                }
            ),
            errors=errors,
        )

    async def async_step_edit_smart_plugs(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        group, index, current = self._edit_context(CONF_SMART_PLUGS)
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                on_command = json.loads(user_input["on_command"])
                off_command = json.loads(user_input["off_command"])
            except json.JSONDecodeError:
                errors["base"] = "invalid_json"
            else:
                try:
                    await self._validate_ecoflow_device(user_input["serial"])
                except Exception:  # noqa: BLE001
                    errors["base"] = "cannot_connect"
                else:
                    item = {
                        **current,
                        "name": user_input["name"],
                        "serial": user_input["serial"],
                        "charges": user_input["charges"],
                        "on_command": on_command,
                        "off_command": off_command,
                    }
                    return self._replace_device(group, index, item)
        return self.async_show_form(
            step_id="edit_smart_plugs",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "name", default=current.get("name", "Delta Pro laadstekker")
                    ): str,
                    vol.Required("serial", default=current.get("serial", "")): str,
                    vol.Required(
                        "charges", default=current.get("charges", "")
                    ): vol.In(self._battery_choices() or {"": "Geen batterij toegevoegd"}),
                    vol.Required(
                        "on_command",
                        default=json.dumps(
                            current.get("on_command", DEFAULT_SMART_PLUG_ON_COMMAND)
                        ),
                    ): str,
                    vol.Required(
                        "off_command",
                        default=json.dumps(
                            current.get("off_command", DEFAULT_SMART_PLUG_OFF_COMMAND)
                        ),
                    ): str,
                }
            ),
            errors=errors,
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
        self.hass.config_entries.async_update_entry(
            self._entry, data=merged, options={}
        )
        self.hass.async_create_task(
            self.hass.config_entries.async_reload(self._entry.entry_id)
        )
        return self.async_create_entry(title="", data={})

    def _edit_context(self, expected_group: str) -> tuple[str, int, dict[str, Any]]:
        if self._pending_edit is None:
            raise ValueError("No device selected")
        group, index = self._pending_edit
        if group != expected_group:
            raise ValueError("Unexpected device group")
        item = self._settings()[group][index]
        return group, index, item

    def _replace_device(
        self, group: str, index: int, item: dict[str, Any]
    ) -> config_entries.FlowResult:
        values = self._settings()
        values[group][index] = item
        self._pending_edit = None
        return self._save(values)

    def _save_imported_ecoflow_device(self) -> config_entries.FlowResult:
        if self._pending_import_config is None:
            raise ValueError("No imported EcoFlow device selected")
        values = self._settings()
        config = self._pending_import_config
        device_type = config["device_type"]
        if device_type in ("delta_pro", "delta_pro_3"):
            values.setdefault(CONF_BATTERIES, []).append(
                {
                    "name": config["name"],
                    "model": "Delta Pro 3"
                    if device_type == "delta_pro_3"
                    else "Delta Pro",
                    "serial": config["serial"],
                    "quotas": DEFAULT_BATTERY_QUOTAS,
                }
            )
        elif device_type == "powerstream":
            values.setdefault(CONF_POWERSTREAMS, []).append(
                {
                    "name": config["name"],
                    "serial": config["serial"],
                    "max_watts": config["max_watts"],
                    "phase": config["phase"],
                    "command": DEFAULT_POWERSTREAM_COMMAND,
                }
            )
        else:
            values.setdefault(CONF_SMART_PLUGS, []).append(
                {
                    "name": config["name"],
                    "serial": config["serial"],
                    "charges": config["charges"],
                    "on_command": DEFAULT_SMART_PLUG_ON_COMMAND,
                    "off_command": DEFAULT_SMART_PLUG_OFF_COMMAND,
                }
            )
        self._pending_import_device = None
        self._pending_import_config = None
        return self._save(values)

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

    async def _validate_ecoflow_device(self, serial: str) -> None:
        response = await self._ecoflow_client().get_devices()
        serials = _extract_ecoflow_serials(response)
        if serials and serial not in serials:
            raise ValueError("device_not_found")

    async def _fetch_ecoflow_devices(self) -> list[dict[str, Any]]:
        response = await self._ecoflow_client().get_devices()
        return _extract_ecoflow_devices(response)

    def _ecoflow_client(self) -> EcoFlowCloudClient:
        from .api.ecoflow import EcoFlowCloudClient

        settings = self._settings()
        return EcoFlowCloudClient(
            async_get_clientsession(self.hass),
            settings[CONF_ECOFLOW_HOST],
            settings[CONF_ACCESS_KEY],
            settings[CONF_SECRET_KEY],
        )

    def _import_device_choices(self, devices: list[dict[str, Any]]) -> dict[str, str]:
        existing = self._configured_ecoflow_serials()
        choices: dict[str, str] = {}
        for device in devices:
            serial = _ecoflow_serial(device)
            if not serial or serial in existing:
                continue
            choices[serial] = f"{_ecoflow_name(device)} ({serial})"
        return choices

    def _configured_ecoflow_serials(self) -> set[str]:
        values = self._settings()
        serials: set[str] = set()
        for group in (CONF_BATTERIES, CONF_POWERSTREAMS, CONF_SMART_PLUGS):
            for item in values.get(group, []):
                if item.get("serial"):
                    serials.add(str(item["serial"]))
        return serials

    def _battery_choices(self) -> dict[str, str]:
        choices: dict[str, str] = {}
        for item in self._settings().get(CONF_BATTERIES, []):
            serial = item.get("serial")
            name = item.get("name", serial)
            if serial:
                choices[str(serial)] = f"{name} ({serial})"
        return choices

    def _homewizard_ha_configured(self, device_id: str) -> bool:
        for item in self._settings().get(CONF_HOMEWIZARD_METERS, []):
            if item.get("source") == "homeassistant" and item.get("device_id") == device_id:
                return True
        return False

    def _homewizard_ha_devices(self) -> dict[str, dict[str, Any]]:
        entity_registry = er.async_get(self.hass)
        device_registry = dr.async_get(self.hass)
        devices: dict[str, dict[str, Any]] = {}
        for entity in entity_registry.entities.values():
            if entity.platform != "homewizard" or not entity.device_id:
                continue
            device = device_registry.async_get(entity.device_id)
            name = (
                device.name_by_user
                if device and device.name_by_user
                else device.name
                if device and device.name
                else entity.device_id
            )
            item = devices.setdefault(
                entity.device_id,
                {
                    "name": name,
                    "model": device.model if device else None,
                    "label": f"{name} ({device.model or 'HomeWizard'})"
                    if device
                    else name,
                    "entities": {},
                },
            )
            role = _homewizard_entity_role(entity)
            if role:
                item["entities"].setdefault(role, entity.entity_id)
        return {
            device_id: item
            for device_id, item in devices.items()
            if item["entities"].get("power") or any(
                item["entities"].get(key)
                for key in ("power_l1", "power_l2", "power_l3")
            )
        }

    async def _validate_sma_device(self, device: dict[str, Any]) -> None:
        from .api.sma_cloud import read_sma_device

        settings = self._settings()
        await read_sma_device(
            async_get_clientsession(self.hass),
            settings[CONF_SMA_API_HOST],
            settings[CONF_SMA_TOKEN],
            settings[CONF_SMA_PLANT_ID],
            device,
            settings[CONF_SMA_ENDPOINT],
        )


def _extract_ecoflow_serials(response: dict[str, Any]) -> set[str]:
    """Extract serial numbers from EcoFlow's device-list response variants."""
    return {
        serial
        for serial in (_ecoflow_serial(device) for device in _extract_ecoflow_devices(response))
        if serial
    }


def _extract_ecoflow_devices(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract device dictionaries from EcoFlow device-list response variants."""
    devices: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if _ecoflow_serial(value):
                devices.append(value)
                return
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(response.get("data", response))
    return devices


def _homewizard_entity_role(entity: Any) -> str | None:
    text = " ".join(
        str(value or "").lower()
        for value in (
            getattr(entity, "translation_key", None),
            getattr(entity, "original_name", None),
            getattr(entity, "name", None),
            getattr(entity, "unique_id", None),
            getattr(entity, "entity_id", None),
        )
    )
    compact = text.replace("_", " ").replace("-", " ")
    if "voltage" in compact or "spanning" in compact:
        if "l1" in compact or "phase 1" in compact:
            return "voltage_l1"
        if "l2" in compact or "phase 2" in compact:
            return "voltage_l2"
        if "l3" in compact or "phase 3" in compact:
            return "voltage_l3"
    if "current" in compact or "stroom" in compact:
        if "l1" in compact or "phase 1" in compact:
            return "current_l1"
        if "l2" in compact or "phase 2" in compact:
            return "current_l2"
        if "l3" in compact or "phase 3" in compact:
            return "current_l3"
    if "power" in compact or "vermogen" in compact:
        if "import" in compact and "energy" in compact:
            return "energy_import"
        if "export" in compact and "energy" in compact:
            return "energy_export"
        if "l1" in compact or "phase 1" in compact:
            return "power_l1"
        if "l2" in compact or "phase 2" in compact:
            return "power_l2"
        if "l3" in compact or "phase 3" in compact:
            return "power_l3"
        if "active" in compact or "total" in compact or "w" in compact:
            return "power"
    if "energy" in compact or "kwh" in compact:
        if "import" in compact and ("t1" in compact or "tariff 1" in compact):
            return "energy_import_t1"
        if "import" in compact and ("t2" in compact or "tariff 2" in compact):
            return "energy_import_t2"
        if "export" in compact and ("t1" in compact or "tariff 1" in compact):
            return "energy_export_t1"
        if "export" in compact and ("t2" in compact or "tariff 2" in compact):
            return "energy_export_t2"
        if "import" in compact:
            return "energy_import"
        if "export" in compact:
            return "energy_export"
    return None


def _ecoflow_serial(device: dict[str, Any]) -> str:
    for key in ("sn", "serial", "serialNumber", "deviceSn"):
        value = device.get(key)
        if value:
            return str(value)
    return ""


def _ecoflow_name(device: dict[str, Any]) -> str:
    for key in ("deviceName", "name", "productName", "model"):
        value = device.get(key)
        if value:
            return str(value)
    serial = _ecoflow_serial(device)
    return f"EcoFlow {serial}" if serial else "EcoFlow apparaat"
