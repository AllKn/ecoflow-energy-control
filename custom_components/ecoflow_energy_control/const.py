"""Constants for EcoFlow Energy Control."""

from __future__ import annotations

DOMAIN = "ecoflow_energy_control"

CONF_ACCESS_KEY = "access_key"
CONF_SECRET_KEY = "secret_key"
CONF_ECOFLOW_HOST = "ecoflow_host"
CONF_PRICE_URL = "price_url"
CONF_PRICE_AREA = "price_area"
CONF_SMA_INVERTERS = "sma_inverters"
CONF_BATTERIES = "batteries"
CONF_POWERSTREAMS = "powerstreams"
CONF_SMART_PLUGS = "smart_plugs"
CONF_DRY_RUN = "dry_run"
CONF_SMA_API_HOST = "sma_api_host"
CONF_SMA_TOKEN = "sma_token"
CONF_SMA_PLANT_ID = "sma_plant_id"
CONF_SMA_ENDPOINT = "sma_endpoint"

DEFAULT_ECOFLOW_HOST = "https://api-e.ecoflow.com"
DEFAULT_PRICE_URL = "https://api.stekker.app/api/v1/market_price_forecast?region=NL"
DEFAULT_SMA_API_HOST = "https://api.sma.energy"
DEFAULT_SMA_ENDPOINT = "/monitoring/v1/plants/{plant_id}/devices/{device_id}/measurements/recent"
DEFAULT_SCAN_INTERVAL = 60

SERVICE_SET_POWERSTREAM_WATTS = "set_powerstream_watts"
SERVICE_APPLY_STRATEGY = "apply_strategy"
SERVICE_SET_SMART_PLUG = "set_smart_plug"

ATTR_SERIAL = "serial"
ATTR_WATTS = "watts"
ATTR_ON = "on"

STRATEGY_SELF_USE = "self_use"
STRATEGY_EXPORT = "export"
STRATEGY_IDLE = "idle"
STRATEGIES = [STRATEGY_SELF_USE, STRATEGY_EXPORT, STRATEGY_IDLE]

DEFAULT_POWERSTREAM_COMMAND = {
    "id": 1,
    "version": "1.0",
    "moduleType": 1,
    "operateType": "WN511_SET_PERMANENT_WATTS_PACK",
    "params": {"permanentWatts": "{{ watts }}"},
}

DEFAULT_BATTERY_QUOTAS = [
    "pd.soc",
    "pd.inputWatts",
    "pd.outputWatts",
    "inv.inputWatts",
    "pd.invOutWatts",
    "bms_bmsStatus.cycSoh",
    "bms_emsStatus.chgRemainTime",
    "bms_emsStatus.dsgRemainTime",
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
