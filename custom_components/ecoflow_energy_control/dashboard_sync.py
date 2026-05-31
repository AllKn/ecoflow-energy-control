"""Synchronize the shipped EEC Lovelace dashboard into Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components import frontend
from homeassistant.components.lovelace import dashboard as lovelace_dashboard
from homeassistant.components.lovelace.const import (
    CONF_ALLOW_SINGLE_WORD,
    CONF_ICON,
    CONF_REQUIRE_ADMIN,
    CONF_SHOW_IN_SIDEBAR,
    CONF_TITLE,
    CONF_URL_PATH,
    DOMAIN as LOVELACE_DOMAIN,
    LOVELACE_DATA,
    MODE_STORAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.yaml import load_yaml_dict

from .const import APP_VERSION

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "ecoflow-app-dashboard"
DASHBOARD_TITLE = f"Ecoflow App dashboard [{APP_VERSION}]"
DASHBOARD_ICON = "mdi:view-dashboard"
DASHBOARD_FILE = "dashboard.yaml"


async def async_sync_shipped_dashboard(hass: HomeAssistant) -> None:
    """Create or update the EEC dashboard from the shipped YAML."""
    try:
        dashboard_config = await hass.async_add_executor_job(_load_dashboard_yaml)
        item = await _async_upsert_dashboard_metadata(hass)
        await _async_save_dashboard_config(hass, item, dashboard_config)
    except (HomeAssistantError, OSError, ValueError, TypeError) as err:
        _LOGGER.warning("Could not synchronize EEC dashboard: %s", err)


def _load_dashboard_yaml() -> dict[str, Any]:
    """Load the dashboard YAML bundled inside the integration."""
    path = Path(__file__).with_name(DASHBOARD_FILE)
    config = load_yaml_dict(path)
    if not isinstance(config.get("views"), list):
        raise ValueError(f"{DASHBOARD_FILE} does not contain Lovelace views")
    return config


async def _async_upsert_dashboard_metadata(hass: HomeAssistant) -> dict[str, Any]:
    """Ensure the dashboard exists in Home Assistant's Lovelace dashboard list."""
    collection = lovelace_dashboard.DashboardsCollection(hass)
    await collection.async_load()
    desired = {
        CONF_ICON: DASHBOARD_ICON,
        CONF_REQUIRE_ADMIN: False,
        CONF_SHOW_IN_SIDEBAR: True,
        CONF_TITLE: DASHBOARD_TITLE,
    }
    for item in collection.async_items():
        if item.get(CONF_URL_PATH) != DASHBOARD_URL_PATH:
            continue
        update = {key: value for key, value in desired.items() if item.get(key) != value}
        if update:
            await collection.async_update_item(item["id"], update)
            return {**item, **update}
        return item

    return await collection.async_create_item(
        {
            **desired,
            CONF_ALLOW_SINGLE_WORD: True,
            CONF_URL_PATH: DASHBOARD_URL_PATH,
        }
    )


async def _async_save_dashboard_config(
    hass: HomeAssistant, item: dict[str, Any], dashboard_config: dict[str, Any]
) -> None:
    """Persist the Lovelace config and refresh the live panel when available."""
    lovelace_data = hass.data.get(LOVELACE_DATA)
    storage = None
    if lovelace_data is not None:
        storage = lovelace_data.dashboards.get(DASHBOARD_URL_PATH)
        if storage is None:
            storage = lovelace_dashboard.LovelaceStorage(hass, item)
            lovelace_data.dashboards[DASHBOARD_URL_PATH] = storage
        else:
            storage.config = item
    else:
        storage = lovelace_dashboard.LovelaceStorage(hass, item)

    await storage.async_save(dashboard_config)

    if lovelace_data is not None:
        frontend.async_register_built_in_panel(
            hass,
            LOVELACE_DOMAIN,
            frontend_url_path=DASHBOARD_URL_PATH,
            require_admin=False,
            show_in_sidebar=True,
            sidebar_title=DASHBOARD_TITLE,
            sidebar_icon=DASHBOARD_ICON,
            config={"mode": MODE_STORAGE},
            update=frontend.async_panel_exists(hass, DASHBOARD_URL_PATH),
        )
