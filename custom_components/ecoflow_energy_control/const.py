"""Constants for EcoFlow Energy Control."""

from __future__ import annotations

DOMAIN = "ecoflow_energy_control"
APP_NAME = "EEC app"
APP_VERSION = "0.5.167"
LEGACY_DASHBOARD_OBJECT_PREFIX = "ecoflow_energy_control_applicatie"

CONF_ACCESS_KEY = "access_key"
CONF_SECRET_KEY = "secret_key"
CONF_ECOFLOW_HOST = "ecoflow_host"
CONF_PRICE_URL = "price_url"
CONF_PRICE_AREA = "price_area"
CONF_PRICE_PROVIDER = "price_provider"
CONF_PRICE_SOURCE = "price_source"
CONF_PRICE_INTERVAL = "price_interval"
CONF_PRICE_SURCHARGE = "price_surcharge"
CONF_PRICE_INCL_VAT = "price_incl_vat"
CONF_SMA_INVERTERS = "sma_inverters"
CONF_BATTERIES = "batteries"
CONF_POWERSTREAMS = "powerstreams"
CONF_SMART_PLUGS = "smart_plugs"
CONF_HOMEWIZARD_METERS = "homewizard_meters"
CONF_DRY_RUN = "dry_run"
CONF_SMA_API_HOST = "sma_api_host"
CONF_SMA_TOKEN = "sma_token"
CONF_SMA_PLANT_ID = "sma_plant_id"
CONF_SMA_ENDPOINT = "sma_endpoint"
CONF_WEATHER_CITY = "weather_city"

DEFAULT_ECOFLOW_HOST = "https://api-e.ecoflow.com"
DEFAULT_PRICE_PROVIDER = "quatt-energy"
DEFAULT_PRICE_SOURCE = "energyzero"
DEFAULT_PRICE_INTERVAL = "hourly"
DEFAULT_PRICE_SURCHARGE = 0.015
DEFAULT_PRICE_INCL_VAT = False
DEFAULT_PRICE_URL = ""
DEFAULT_SMA_API_HOST = "https://api.sma.energy"
DEFAULT_SMA_ENDPOINT = "/monitoring/v1/plants/{plant_id}/devices/{device_id}/measurements/recent"
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_HOMEWIZARD_ROLE = "solar_total"
DEFAULT_WEATHER_CITY = "Amsterdam"
WEATHER_CITIES = {
    "Amsterdam": (52.3676, 4.9041),
    "Rotterdam": (51.9244, 4.4777),
    "Den Haag": (52.0705, 4.3007),
    "Utrecht": (52.0907, 5.1214),
    "Eindhoven": (51.4416, 5.4697),
    "Groningen": (53.2194, 6.5665),
    "Maastricht": (50.8514, 5.6910),
    "Arnhem": (51.9851, 5.8987),
    "Zwolle": (52.5168, 6.0830),
    "Middelburg": (51.4988, 3.6100),
}

SERVICE_SET_POWERSTREAM_WATTS = "set_powerstream_watts"
SERVICE_APPLY_STRATEGY = "apply_strategy"
SERVICE_APPLY_BEST_SCENARIO = "apply_best_scenario"
SERVICE_SET_SMART_PLUG = "set_smart_plug"

ATTR_SERIAL = "serial"
ATTR_WATTS = "watts"
ATTR_ON = "on"

STRATEGY_SELF_USE = "self_use"
STRATEGY_EXPORT = "export"
STRATEGY_BUFFER_50 = "buffer_50"
STRATEGY_IDLE = "idle"
STRATEGIES = [STRATEGY_SELF_USE, STRATEGY_EXPORT, STRATEGY_BUFFER_50, STRATEGY_IDLE]
POWERSTREAM_STRATEGY_SELF_USE = "max_self_use"
POWERSTREAM_STRATEGY_TRADING = "max_trading"
POWERSTREAM_STRATEGY_BUFFER_50 = "buffer_50"
POWERSTREAM_STRATEGY_IDLE = "idle"
POWERSTREAM_STRATEGIES = [
    POWERSTREAM_STRATEGY_SELF_USE,
    POWERSTREAM_STRATEGY_TRADING,
    POWERSTREAM_STRATEGY_BUFFER_50,
    POWERSTREAM_STRATEGY_IDLE,
]

DEFAULT_POWERSTREAM_COMMAND = {
    "id": 1,
    "version": "1.0",
    "cmdCode": "WN511_SET_PERMANENT_WATTS_PACK",
    "params": {"permanentWatts": "{{ deciwatts }}"},
}

DEFAULT_BATTERY_QUOTAS = [
    "pd.soc",
    "ems.soc",
    "bms.soc",
    "bms_emsStatus.soc",
    "bms_bmsStatus.soc",
    "soc",
    "socLevel",
    "batteryLevel",
    "pd.inputWatts",
    "pd.outputWatts",
    "pd.wattsInSum",
    "pd.wattsOutSum",
    "pd.acInWatts",
    "pd.acOutWatts",
    "pd.dcInWatts",
    "pd.dcOutWatts",
    "pd.solarWatts",
    "mppt.inWatts",
    "mppt.inputWatts",
    "mppt.inputPower",
    "pv.inputWatts",
    "pv.inputPower",
    "pvInWatts",
    "pvInPower",
    "bms_emsStatus.inputWatts",
    "bms_emsStatus.outputWatts",
    "bms_emsStatus.wattsInSum",
    "bms_emsStatus.wattsOutSum",
    "inv.inputWatts",
    "inv.outputWatts",
    "inv.acInWatts",
    "inv.acOutWatts",
    "pd.invOutWatts",
    "bms_bmsStatus.cycSoh",
    "bms_emsStatus.chgRemainTime",
    "bms_emsStatus.dsgRemainTime",
]

DEFAULT_POWERSTREAM_QUOTAS = [
    "permanentWatts",
    "inv.outputWatts",
    "inv.inputWatts",
    "pv.inputWatts",
    "bat.inputWatts",
    "bat.outputWatts",
]

DEFAULT_SMART_PLUG_ON_COMMAND = {
    "id": 1,
    "version": "1.0",
    "moduleType": 1,
    "operateType": "TCP_SET_SWITCH",
    "params": {"enabled": True},
}

DEFAULT_SMART_PLUG_OFF_COMMAND = {
    "id": 1,
    "version": "1.0",
    "moduleType": 1,
    "operateType": "TCP_SET_SWITCH",
    "params": {"enabled": False},
}
