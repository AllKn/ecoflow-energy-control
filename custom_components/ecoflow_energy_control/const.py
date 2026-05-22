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
CONF_DRY_RUN = "dry_run"

DEFAULT_ECOFLOW_HOST = "https://api-e.ecoflow.com"
DEFAULT_PRICE_URL = "https://enever.nl/api/stroomprijs_vandaag.php"
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_SMA_PORT = 502
DEFAULT_SMA_UNIT_ID = 3

SERVICE_SET_POWERSTREAM_WATTS = "set_powerstream_watts"
SERVICE_APPLY_STRATEGY = "apply_strategy"

ATTR_SERIAL = "serial"
ATTR_WATTS = "watts"

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

