"""Readiness checks for the simple dashboard flow."""

from __future__ import annotations

from typing import Any

DEFAULT_SETUP_PRICE_SOURCE = "energyzero"


def dashboard_readiness(data: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    """Summarize whether the dashboard has enough data for useful decisions."""
    checks = [
        _check_price_data(data),
        _check_batteries(data, settings),
        _check_powerstreams(data, settings),
        _check_solar(data, settings),
        _check_p1_history(data, settings),
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
    check_map = {item["key"]: item for item in checks}
    insight = _insight_state(check_map)
    return {
        "status": status,
        "ready": status == "klaar",
        "insight_ready": insight["ready"],
        "insight_status": insight["status"],
        "insight_next_step": insight["next_step"],
        "insight_checks": insight["checks"],
        "control_ready": status == "klaar",
        "next_step": _next_step(blocking or warnings),
        "score": round(
            sum(1 for item in checks if item["status"] == "klaar") / len(checks) * 100,
            0,
        ),
        "blocking": [item["key"] for item in blocking],
        "warnings": [item["key"] for item in warnings],
        "checks": checks,
    }


def _insight_state(checks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    required = ("prices", "batteries")
    missing = [
        key
        for key in required
        if (checks.get(key) or {}).get("status") != "klaar"
    ]
    if missing:
        first = checks.get(missing[0]) or {}
        return {
            "ready": False,
            "status": "actie nodig",
            "next_step": _next_step([first]),
            "checks": list(required),
        }
    return {
        "ready": True,
        "status": "basis klaar",
        "next_step": "basisinzicht klaar",
        "checks": list(required),
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
        label = _source_label(str(first_check.get("key") or "bron"))
        summary = f"{label}: {first_check.get('message')}"
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
        "first_issue_label": _source_label(str(first_key)) if first_key else None,
        "first_issue_status": first_check.get("status") if first_check else None,
        "first_issue_message": first_check.get("message") if first_check else None,
        "ready_sources": ok_count,
        "total_sources": total_count,
        "blocking": readiness.get("blocking"),
        "warnings": readiness.get("warnings"),
    }


def live_missing_summary(proof: dict[str, Any], fallback: Any) -> str:
    """Return the most useful missing live proof message."""
    label = proof.get("first_missing_label")
    message = proof.get("first_missing_message")
    if label and message:
        return f"{label}: {message}"
    return str(fallback or "controleer Datacheck")


def _source_label(key: str) -> str:
    return {
        "prices": "prijzen",
        "batteries": "batterijen",
        "powerstreams": "PowerStreams",
        "solar": "netto opwek",
        "p1_history": "P1 historie",
        "weather": "weer",
        "scenarios": "scenario's",
        "execution": "sturing",
    }.get(key, key)


def next_user_step(
    readiness: dict[str, Any],
    setup: dict[str, Any],
    action: dict[str, Any],
    *,
    dry_run: bool,
    choice: dict[str, Any] | None = None,
    live_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the single most useful user-facing next step."""
    choice = choice or {}
    live_proof = live_proof or {}
    if not setup.get("ready_for_basic_insight"):
        step = str(setup.get("next_step") or "basis instellen")
        return _user_step(
            "basis nodig",
            step,
            "setup",
            "basisinzicht vereist minimaal een batterij; EnergyZero is de standaard prijsbron",
            setup,
            readiness,
            action,
            choice,
        )
    if not readiness.get("insight_ready"):
        step = str(readiness.get("insight_next_step") or readiness.get("next_step"))
        return _user_step(
            "data nodig",
            step,
            "data",
            "prijsdata en batterij-SoC zijn nodig voor basisinzicht",
            setup,
            readiness,
            action,
            choice,
        )
    if not setup.get("ready_for_powerstream_control"):
        return _user_step(
            "basis klaar",
            "PowerStream toevoegen voor automatische sturing",
            "setup",
            "basisinzicht werkt al; PowerStream maakt sturen mogelijk",
            setup,
            readiness,
            action,
            choice,
        )
    if readiness.get("status") == "actie nodig":
        step = live_missing_summary(
            live_proof, readiness.get("next_step") or "controleer datacheck"
        )
        return _user_step(
            "actie nodig",
            step,
            "data",
            "een live databron of commandofout blokkeert sturing",
            setup,
            readiness,
            action,
            choice,
        )
    if dry_run and readiness.get("control_ready"):
        return _user_step(
            "testmodus",
            "zet testmodus uit om echt te sturen",
            "control",
            "de app simuleert nog en stuurt geen PowerStreams aan",
            setup,
            readiness,
            action,
            choice,
        )
    if choice.get("state") == "wijkt af":
        return _user_step(
            "keuze aanpassen",
            str(choice.get("summary") or "laat Scenario het beste advies volgen"),
            "scenario",
            "de gekozen strategie wijkt af van het berekende beste scenario",
            setup,
            readiness,
            action,
            choice,
        )
    if action.get("can_execute"):
        return _user_step(
            "startbaar",
            f"druk Advies: {action.get('summary') or 'pas beste scenario toe'}",
            "control",
            "er is een uitvoerbaar PowerStream-commando beschikbaar",
            setup,
            readiness,
            action,
            choice,
        )
    if action.get("action_type") in {"wait", "error"}:
        return _user_step(
            "wachten",
            str(action.get("summary") or readiness.get("next_step") or "wacht"),
            "control",
            str(action.get("blocked_by") or "de app wacht tot sturen veilig is"),
            setup,
            readiness,
            action,
            choice,
        )
    if not setup.get("ready_for_full_optimization"):
        return _user_step(
            "optimaliseren",
            str(setup.get("next_step") or readiness.get("next_step")),
            "setup",
            "sturing kan al; deze stap verbetert de optimalisatie",
            setup,
            readiness,
            action,
            choice,
        )
    if readiness.get("status") == "gedeeltelijk":
        return _user_step(
            "optimaliseren",
            str(readiness.get("next_step") or "controleer waarschuwingen"),
            "data",
            "de basis werkt; een waarschuwing kan de kwaliteit verbeteren",
            setup,
            readiness,
            action,
            choice,
        )
    return _user_step(
        "klaar",
        "geen actie nodig",
        "none",
        "basisinzicht en sturing zijn klaar",
        setup,
        readiness,
        action,
        choice,
    )


def simple_flow_stage(
    readiness: dict[str, Any],
    setup: dict[str, Any],
    action: dict[str, Any],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    """Return the simplest user-facing stage for the main dashboard."""
    if not setup.get("ready_for_basic_insight"):
        return _flow_stage(
            "basis nodig",
            str(setup.get("next_step") or "batterij instellen"),
            "setup",
            "basisinzicht vereist minimaal een batterij; EnergyZero is de standaard prijsbron",
            readiness,
            setup,
            action,
            dry_run,
        )
    if not readiness.get("insight_ready"):
        return _flow_stage(
            "data nodig",
            str(readiness.get("insight_next_step") or readiness.get("next_step")),
            "data",
            "prijsdata en batterij-SoC zijn nog niet live bewezen",
            readiness,
            setup,
            action,
            dry_run,
        )
    if not setup.get("ready_for_powerstream_control"):
        return _flow_stage(
            "inzicht klaar",
            "basisinzichten werken; PowerStream toevoegen voor sturing",
            "insight",
            "met batterij en standaard prijsdata kan de app al inzicht geven",
            readiness,
            setup,
            action,
            dry_run,
        )
    if not readiness.get("control_ready"):
        return _flow_stage(
            "sturing beperkt",
            str(readiness.get("next_step") or "controleer Datacheck"),
            "data",
            "een live bron of sturing is nog niet volledig bewezen",
            readiness,
            setup,
            action,
            dry_run,
        )
    if dry_run:
        return _flow_stage(
            "testmodus",
            "data en sturing klaar; testmodus staat nog aan",
            "control",
            "de app simuleert nog en stuurt geen PowerStreams aan",
            readiness,
            setup,
            action,
            dry_run,
        )
    if action.get("can_execute"):
        return _flow_stage(
            "startbaar",
            f"Advies: {action.get('summary') or 'pas beste scenario toe'}",
            "control",
            "er is een uitvoerbaar PowerStream-commando beschikbaar",
            readiness,
            setup,
            action,
            dry_run,
        )
    if not setup.get("ready_for_full_optimization"):
        return _flow_stage(
            "optimaliseren",
            str(setup.get("next_step") or "optionele bron toevoegen"),
            "setup",
            "basis en sturing kunnen werken; deze stap verbetert de optimalisatie",
            readiness,
            setup,
            action,
            dry_run,
        )
    return _flow_stage(
        "sturing klaar",
        str(action.get("summary") or "geen actie nodig"),
        "ready",
        "basisinzicht en PowerStream-sturing zijn live klaar",
        readiness,
        setup,
        action,
        dry_run,
    )


def _flow_stage(
    state: str,
    summary: str,
    category: str,
    reason: str,
    readiness: dict[str, Any],
    setup: dict[str, Any],
    action: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "state": state,
        "summary": summary,
        "category": category,
        "reason": reason,
        "dry_run": dry_run,
        "setup_state": setup.get("state"),
        "setup_progress": setup.get("progress"),
        "ready_for_basic_insight": setup.get("ready_for_basic_insight"),
        "ready_for_powerstream_control": setup.get("ready_for_powerstream_control"),
        "ready_for_full_optimization": setup.get("ready_for_full_optimization"),
        "readiness_status": readiness.get("status"),
        "readiness_score": readiness.get("score"),
        "insight_ready": readiness.get("insight_ready"),
        "control_ready": readiness.get("control_ready"),
        "next_step": readiness.get("next_step"),
        "action_summary": action.get("summary"),
        "can_execute": action.get("can_execute"),
        "command_required": action.get("command_required"),
        "blocked_by": action.get("blocked_by"),
    }


def _user_step(
    state: str,
    summary: str,
    category: str,
    reason: str,
    setup: dict[str, Any],
    readiness: dict[str, Any],
    action: dict[str, Any],
    choice: dict[str, Any],
) -> dict[str, Any]:
    return {
        "state": state,
        "summary": summary,
        "category": category,
        "reason": reason,
        "setup_state": setup.get("state"),
        "setup_progress": setup.get("progress"),
        "next_setup_step": setup.get("next_step"),
        "ready_for_basic_insight": setup.get("ready_for_basic_insight"),
        "ready_for_powerstream_control": setup.get("ready_for_powerstream_control"),
        "ready_for_full_optimization": setup.get("ready_for_full_optimization"),
        "readiness_status": readiness.get("status"),
        "readiness_score": readiness.get("score"),
        "readiness_next_step": readiness.get("next_step"),
        "insight_ready": readiness.get("insight_ready"),
        "control_ready": readiness.get("control_ready"),
        "action_type": action.get("action_type"),
        "action_summary": action.get("summary"),
        "can_execute": action.get("can_execute"),
        "command_required": action.get("command_required"),
        "blocked_by": action.get("blocked_by"),
        "choice_state": choice.get("state"),
        "choice_summary": choice.get("summary"),
    }


def setup_state(settings: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
    """Return minimal setup progress for the main dashboard."""
    batteries = _configured_setup_items(settings, "batteries")
    powerstreams = _configured_setup_items(settings, "powerstreams")
    homewizard = _configured_setup_items(settings, "homewizard_meters")
    sma = _configured_setup_items(settings, "sma_inverters")
    solar_sources = homewizard + sma
    price_source = settings.get("price_source") or DEFAULT_SETUP_PRICE_SOURCE
    missing: list[str] = []
    optional: list[str] = []
    if not batteries:
        missing.append("batterij toevoegen")
    if not powerstreams:
        optional.append("PowerStream toevoegen")
    if not solar_sources:
        optional.append("zonmeter toevoegen")
    if not settings.get("weather_city"):
        optional.append("weerstad instellen")
    if missing:
        state = "actie nodig"
        next_step = missing[0]
        next_step_kind = "verplicht"
    elif optional:
        state = "basis klaar"
        next_step = optional[0]
        next_step_kind = "aanbevolen"
    else:
        state = "compleet"
        next_step = "basisconfiguratie compleet"
        next_step_kind = "klaar"
    required_done = 1 - len(missing)
    optional_done = 3 - len(optional)
    progress = round((required_done * 60 + optional_done * 13.33), 0)
    ready_for_basic_insight = not missing
    ready_for_powerstream_control = ready_for_basic_insight and bool(powerstreams)
    ready_for_full_optimization = ready_for_basic_insight and not optional
    if not ready_for_basic_insight:
        current_capability = "nog geen basisinzicht"
    elif not ready_for_powerstream_control:
        current_capability = "basisinzicht beschikbaar"
    elif not ready_for_full_optimization:
        current_capability = "sturing beschikbaar"
    else:
        current_capability = "volledige optimalisatie beschikbaar"
    return {
        "state": state,
        "next_step": next_step,
        "next_step_kind": next_step_kind,
        "summary": f"{state}: {next_step}",
        "current_capability": current_capability,
        "progress": max(0, min(100, int(progress))),
        "ready_for_basic_insight": ready_for_basic_insight,
        "ready_for_powerstream_control": ready_for_powerstream_control,
        "ready_for_full_optimization": ready_for_full_optimization,
        "basic_requirements": ["batterij"],
        "control_requirements": ["PowerStream"],
        "optimization_requirements": ["zonmeter", "weerstad"],
        "required_done": required_done,
        "required_total": 1,
        "optional_done": optional_done,
        "optional_total": 3,
        "missing_required": missing,
        "missing_optional": optional,
        "configured_batteries": len(batteries),
        "configured_powerstreams": len(powerstreams),
        "configured_solar_sources": len(solar_sources),
        "configured_homewizard_meters": len(homewizard),
        "configured_sma_inverters": len(sma),
        "price_source": price_source,
        "price_source_defaulted": not bool(settings.get("price_source") or settings.get("price_url")),
        "custom_price_url": bool(settings.get("price_url")),
        "weather_city": settings.get("weather_city"),
        "dry_run": dry_run,
        "basis": "minimaal: batterij; prijsdata gebruikt standaard EnergyZero; optimaal: PowerStream, zonmeter en weerstad",
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


def _check_p1_history(data: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    configured = [
        item
        for item in settings.get("homewizard_meters", [])
        if item.get("role") == "grid_meter"
    ]
    details = {
        "configured": len(configured),
        "homeassistant_sources": len(
            [item for item in configured if item.get("source") == "homeassistant"]
        ),
        "with_history": 0,
        "missing_history": len(configured),
        "periods_required": ["today", "week", "month"],
    }
    if not configured:
        return _check("p1_history", "klaar", "geen P1/netmeter ingesteld", details)

    if not any(item.get("source") == "homeassistant" for item in configured):
        return _check(
            "p1_history",
            "gedeeltelijk",
            "P1-historie vereist HomeWizard import via HA",
            details,
        )

    meters = data.get("homewizard_meters") or {}
    with_history = 0
    missing: list[str] = []
    incomplete: list[str] = []
    for item in configured:
        reading = _homewizard_reading(meters, item)
        history = reading.get("history") if isinstance(reading, dict) else None
        periods = (history or {}).get("periods") or {}
        if not history or not history.get("available"):
            missing.append(str(item.get("name") or item.get("host") or item.get("device_id")))
            continue
        missing_periods = [
            period
            for period in ("today", "week", "month")
            if (periods.get(period) or {}).get("net_import_kwh") is None
        ]
        if missing_periods:
            incomplete.append(
                f"{item.get('name') or item.get('host') or item.get('device_id')}:"
                f"{','.join(missing_periods)}"
            )
            continue
        with_history += 1

    details["with_history"] = with_history
    details["missing_history"] = max(0, len(configured) - with_history)
    details["missing"] = missing
    details["incomplete"] = incomplete
    if with_history == len(configured):
        return _check("p1_history", "klaar", "P1-historie beschikbaar", details)
    if missing:
        return _check("p1_history", "gedeeltelijk", "P1-historie ontbreekt", details)
    return _check("p1_history", "gedeeltelijk", "P1-historie onvolledig", details)


def _check_weather(data: dict[str, Any]) -> dict[str, Any]:
    weather = data.get("weather") or {}
    hourly = weather.get("hourly") or []
    details = {
        "weather_label": weather.get("weather_label"),
        "weather_hours": len(hourly),
        "shortwave_w_m2": weather.get("shortwave_w_m2"),
    }
    if weather.get("shortwave_w_m2") is None and not hourly:
        return _check("weather", "gedeeltelijk", "weerdata ontbreekt", details)
    if not hourly:
        return _check(
            "weather", "gedeeltelijk", "weergrafiek mist komende uren", details
        )
    if len(hourly) < 12:
        return _check(
            "weather", "gedeeltelijk", "weergrafiek heeft minder dan 12 uur", details
        )
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


def _configured_setup_items(settings: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [
        item
        for item in settings.get(key, [])
        if isinstance(item, dict)
        and any(
            item.get(field)
            for field in ("serial", "host", "device_id", "device", "name")
        )
        and "VUL_HIER" not in str(item)
    ]


def _homewizard_reading(
    readings: dict[str, Any], configured: dict[str, Any]
) -> dict[str, Any]:
    for key in (
        configured.get("name"),
        configured.get("host"),
        configured.get("device_id"),
    ):
        if key and isinstance(readings.get(key), dict):
            return readings[key]
    return {}


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
        "p1_history": "controleer P1 historie",
        "weather": "controleer weerdata",
        "scenarios": "wacht op scenario-berekening",
    }
    label = labels.get(item["key"], item["key"])
    return f"{label}: {item['message']}"
