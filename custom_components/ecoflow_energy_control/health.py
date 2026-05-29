"""Readiness checks for the simple dashboard flow."""

from __future__ import annotations

from typing import Any


def dashboard_readiness(data: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    """Summarize whether the dashboard has enough data for useful decisions."""
    checks = [
        _check_price_data(data),
        _check_batteries(data, settings),
        _check_powerstreams(data, settings),
        _check_solar(data, settings),
        _check_weather(data),
        _check_scenarios(data),
        _check_execution(data, settings),
    ]
    blocking = [item for item in checks if item["status"] == "actie nodig"]
    warnings = [item for item in checks if item["status"] == "gedeeltelijk"]
    if blocking:
        status = "actie nodig"
    elif warnings:
        status = "gedeeltelijk"
    else:
        status = "klaar"
    return {
        "status": status,
        "ready": status == "klaar",
        "next_step": _next_step(blocking or warnings),
        "score": round(
            sum(1 for item in checks if item["status"] == "klaar") / len(checks) * 100,
            0,
        ),
        "blocking": [item["key"] for item in blocking],
        "warnings": [item["key"] for item in warnings],
        "checks": checks,
    }


def source_summary(readiness: dict[str, Any]) -> dict[str, Any]:
    """Return the first relevant source issue or an all-clear summary."""
    checks = readiness.get("checks") or []
    status = str(readiness.get("status") or "onbekend")
    priority = list(readiness.get("blocking") or readiness.get("warnings") or [])
    first_key = priority[0] if priority else None
    first_check = next(
        (item for item in checks if item.get("key") == first_key),
        None,
    )
    ok_count = len([item for item in checks if item.get("status") == "klaar"])
    total_count = len(checks)
    if first_check:
        summary = f"{first_check.get('key')}: {first_check.get('message')}"
    elif total_count:
        summary = f"alle bronnen ok ({ok_count}/{total_count})"
    else:
        summary = "geen bronchecks"
    return {
        "summary": summary,
        "status": status,
        "score": readiness.get("score"),
        "next_step": readiness.get("next_step"),
        "first_issue_key": first_key,
        "first_issue_message": first_check.get("message") if first_check else None,
        "ready_sources": ok_count,
        "total_sources": total_count,
        "blocking": readiness.get("blocking"),
        "warnings": readiness.get("warnings"),
    }


def _check_price_data(data: dict[str, Any]) -> dict[str, Any]:
    prices = data.get("prices") or []
    chart = (data.get("price_summary") or {}).get("chart") or []
    price_now = data.get("price_now")
    details = {
        "price_now": price_now,
        "price_hours": len(prices),
        "chart_hours": len(chart),
    }
    if price_now is None:
        return _check("prices", "actie nodig", "geen actuele prijs", details)
    if len(prices) < 12:
        return _check("prices", "gedeeltelijk", "minder dan 12 prijsuren", details)
    if not chart:
        return _check(
            "prices", "gedeeltelijk", "prijsgrafiek mist komende uren", details
        )
    if len(chart) < 12:
        return _check(
            "prices", "gedeeltelijk", "prijsgrafiek heeft minder dan 12 uur", details
        )
    return _check("prices", "klaar", f"{len(prices)} prijsuren", details)


def _check_batteries(data: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    configured = [
        item
        for item in settings.get("batteries", [])
        if item.get("serial") and "VUL_HIER" not in str(item.get("serial"))
    ]
    configured_serials = [str(item.get("serial")) for item in configured]
    batteries = data.get("batteries") or {}
    details = {
        "configured": len(configured),
        "live": 0,
        "missing": len(configured),
        "with_soc": 0,
        "missing_soc": len(configured),
    }
    if not configured:
        return _check("batteries", "actie nodig", "geen batterijen ingesteld", details)
    telemetry = [
        item
        for serial in configured_serials
        if isinstance((item := batteries.get(serial)), dict)
        and item.get("values")
    ]
    details["live"] = len(telemetry)
    details["missing"] = max(0, len(configured) - len(telemetry))
    with_soc = [
        item
        for item in telemetry
        if _battery_soc_value(item.get("values", {})) is not None
    ]
    details["with_soc"] = len(with_soc)
    details["missing_soc"] = max(0, len(configured) - len(with_soc))
    if not telemetry:
        return _check("batteries", "actie nodig", "geen batterijtelemetrie", details)
    if not with_soc:
        return _check("batteries", "gedeeltelijk", "batterij-SoC ontbreekt", details)
    if len(telemetry) < len(configured):
        return _check(
            "batteries", "gedeeltelijk", "niet alle batterijen hebben data", details
        )
    if len(with_soc) < len(configured):
        return _check(
            "batteries",
            "gedeeltelijk",
            "niet alle batterijen hebben SoC",
            details,
        )
    return _check("batteries", "klaar", f"{len(telemetry)} batterij(en)", details)


def _check_powerstreams(data: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    configured = [
        item
        for item in settings.get("powerstreams", [])
        if item.get("serial") and "VUL_HIER" not in str(item.get("serial"))
    ]
    configured_serials = [str(item.get("serial")) for item in configured]
    powerstreams = data.get("powerstreams") or {}
    details = {
        "configured": len(configured),
        "live": 0,
        "missing": len(configured),
        "missing_link": 0,
        "missing_soc": 0,
        "limited_telemetry": 0,
    }
    if not configured:
        return _check(
            "powerstreams", "gedeeltelijk", "geen PowerStreams ingesteld", details
        )
    available = [
        item
        for serial in configured_serials
        if isinstance((item := powerstreams.get(serial)), dict)
        and not item.get("error")
    ]
    available_serials = [
        serial
        for serial in configured_serials
        if isinstance((item := powerstreams.get(serial)), dict)
        and not item.get("error")
    ]
    details["live"] = len(available)
    details["missing"] = max(0, len(configured) - len(available))
    details["live_serials"] = available_serials
    details["missing_serials"] = [
        serial for serial in configured_serials if serial not in available_serials
    ]
    if not available:
        return _check("powerstreams", "actie nodig", "geen PowerStream data", details)
    if len(available) < len(configured):
        return _check(
            "powerstreams", "gedeeltelijk", "niet alle PowerStreams hebben data", details
        )
    missing_link = [item for item in available if not item.get("battery_serial")]
    details["missing_link"] = len(missing_link)
    if missing_link:
        return _check(
            "powerstreams", "gedeeltelijk", "PowerStream mist gekoppelde accu", details
        )
    missing_soc = [
        item
        for item in available
        if item.get("battery_serial") and item.get("battery_soc") is None
    ]
    details["missing_soc"] = len(missing_soc)
    if missing_soc:
        return _check(
            "powerstreams", "gedeeltelijk", "gekoppelde accu-SoC ontbreekt", details
        )
    missing_telemetry = [item for item in available if not item.get("values")]
    details["limited_telemetry"] = len(missing_telemetry)
    if missing_telemetry:
        return _check(
            "powerstreams", "gedeeltelijk", "PowerStream telemetrie beperkt", details
        )
    return _check(
        "powerstreams", "klaar", f"{len(available)} PowerStream(s)", details
    )


def _check_solar(data: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    configured = settings.get("homewizard_meters") or settings.get("sma_inverters") or []
    details = {
        "configured": len(configured),
        "corrected_solar_power": data.get("corrected_solar_power"),
        "powerstream_export_w": data.get("powerstream_export_w"),
    }
    if not configured:
        return _check("solar", "gedeeltelijk", "geen opwekbron ingesteld", details)
    if data.get("corrected_solar_power") is None:
        return _check("solar", "actie nodig", "netto opwek ontbreekt", details)
    return _check("solar", "klaar", "netto opwek beschikbaar", details)


def _check_weather(data: dict[str, Any]) -> dict[str, Any]:
    weather = data.get("weather") or {}
    details = {
        "weather_label": weather.get("weather_label"),
        "weather_hours": len(weather.get("hourly") or []),
        "shortwave_w_m2": weather.get("shortwave_w_m2"),
    }
    if weather.get("shortwave_w_m2") is None and not weather.get("hourly"):
        return _check("weather", "gedeeltelijk", "weerdata ontbreekt", details)
    return _check(
        "weather", "klaar", weather.get("weather_label") or "weer beschikbaar", details
    )


def _check_scenarios(data: dict[str, Any]) -> dict[str, Any]:
    scenarios = data.get("scenarios") or {}
    details = {"scenario_count": len(scenarios)}
    if not scenarios:
        return _check("scenarios", "actie nodig", "scenario's ontbreken", details)
    if len(scenarios) < 3:
        return _check(
            "scenarios", "gedeeltelijk", "niet alle scenario's berekend", details
        )
    return _check("scenarios", "klaar", f"{len(scenarios)} scenario's", details)


def _check_execution(data: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    powerstreams = _configured_powerstream_data(data, settings)
    details = {
        "dry_run": bool(settings.get("dry_run", True)),
        "last_powerstream_error": data.get("last_powerstream_error"),
        "strategy_errors": 0,
        "throttled": 0,
        "last_powerstream_source": data.get("last_powerstream_source"),
    }
    if data.get("last_powerstream_error"):
        return _check(
            "execution", "actie nodig", "laatste PowerStream command faalde", details
        )
    strategy_errors = [
        item.get("strategy_error")
        for item in powerstreams.values()
        if isinstance(item, dict) and item.get("strategy_error")
    ]
    details["strategy_errors"] = len(strategy_errors)
    if strategy_errors:
        return _check("execution", "actie nodig", "strategie-command faalde", details)
    throttled = [
        item
        for item in powerstreams.values()
        if isinstance(item, dict) and item.get("strategy_throttled")
    ]
    details["throttled"] = len(throttled)
    if throttled:
        return _check(
            "execution", "gedeeltelijk", "wacht op 10-minuten begrenzing", details
        )
    if settings.get("dry_run", True):
        return _check("execution", "gedeeltelijk", "testmodus staat aan", details)
    return _check("execution", "klaar", "sturing actief", details)


def _configured_powerstream_data(
    data: dict[str, Any], settings: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    powerstreams = data.get("powerstreams") or {}
    configured_serials = [
        str(item.get("serial"))
        for item in settings.get("powerstreams", [])
        if item.get("serial") and "VUL_HIER" not in str(item.get("serial"))
    ]
    return {
        serial: item
        for serial in configured_serials
        if isinstance((item := powerstreams.get(serial)), dict)
    }


def _check(
    key: str,
    status: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {"key": key, "status": status, "message": message, "details": details or {}}


def _battery_soc_value(values: dict[str, Any]) -> float | None:
    for key in (
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
    ):
        value = values.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        return max(0.0, min(numeric, 100.0))
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


def _next_step(items: list[dict[str, Any]]) -> str:
    if not items:
        return "klaar voor sturen"
    item = items[0]
    if item["key"] == "execution":
        label = (
            "zet testmodus uit"
            if item["message"] == "testmodus staat aan"
            else "controleer sturing"
        )
        return f"{label}: {item['message']}"
    labels = {
        "prices": "haal prijsdata op",
        "batteries": "controleer EcoFlow batterijdata",
        "powerstreams": "controleer PowerStream koppeling",
        "solar": "controleer netto opwekbron",
        "weather": "controleer weerdata",
        "scenarios": "wacht op scenario-berekening",
    }
    label = labels.get(item["key"], item["key"])
    return f"{label}: {item['message']}"
