"""Local scenario and PowerStream decision helpers."""

from __future__ import annotations

from typing import Any


def powerstream_group_decision(
    strategy: str,
    item: dict[str, Any],
    price_now: float | None,
    bands: dict[str, float | None],
    solar_power_w: float,
) -> dict[str, Any]:
    """Return the suggested PowerStream action for a device group."""
    max_watts = float(item.get("max_watts") or 0)
    if max_watts <= 0:
        max_watts = 800.0
    soc = item.get("battery_soc")
    battery_ready = soc is None or float(soc) > 20
    free_wh = item.get("battery_free_wh")
    can_charge = free_wh is None or float(free_wh) > 100
    can_discharge = battery_ready
    cheap = bands.get("cheap")
    expensive = bands.get("expensive")
    price = float(price_now or 0)
    solar = float(solar_power_w or 0)

    if strategy == "idle":
        return {
            "group_action": "stand-by",
            "suggested_watts": 0,
            "decision_reason": "strategie uit",
            "can_charge": False,
            "can_discharge": False,
            "charge_blocker": "strategie uit",
            "discharge_blocker": "strategie uit",
        }
    if strategy == "max_trading":
        if cheap is not None and price <= cheap and solar > 100 and can_charge:
            return {
                "group_action": "laden",
                "suggested_watts": 0,
                "decision_reason": "lage prijs en zon",
                "can_charge": True,
                "can_discharge": can_discharge,
                "charge_blocker": None,
                "discharge_blocker": None if can_discharge else "accu onder minimum",
            }
        if expensive is not None and price >= expensive and can_discharge:
            return {
                "group_action": "terugleveren",
                "suggested_watts": round(max_watts, 0),
                "decision_reason": "hoge prijs",
                "can_charge": can_charge,
                "can_discharge": True,
                "charge_blocker": None if can_charge else "geen vrije accuruimte",
                "discharge_blocker": None,
            }
        return {
            "group_action": "wachten",
            "suggested_watts": 0,
            "decision_reason": "geen handelsmoment"
            if can_charge
            else "geen vrije accuruimte",
            "can_charge": can_charge,
            "can_discharge": can_discharge,
            "charge_blocker": None if can_charge else "geen vrije accuruimte",
            "discharge_blocker": None if can_discharge else "accu onder minimum",
        }

    if strategy == "buffer_50":
        above_buffer = soc is None or float(soc) > 50
        if expensive is not None and price >= expensive and above_buffer and can_discharge:
            return {
                "group_action": "terugleveren boven buffer",
                "suggested_watts": round(max_watts, 0),
                "decision_reason": "hoge prijs en accu boven 50%",
                "can_charge": can_charge,
                "can_discharge": True,
                "charge_blocker": None if can_charge else "geen vrije accuruimte",
                "discharge_blocker": None,
            }
        return {
            "group_action": "buffer bewaken",
            "suggested_watts": 0,
            "decision_reason": "50% buffer wordt bewaakt"
            if above_buffer
            else "accu op of onder 50%",
            "can_charge": can_charge,
            "can_discharge": can_discharge and above_buffer,
            "charge_blocker": None if can_charge else "geen vrije accuruimte",
            "discharge_blocker": None
            if can_discharge and above_buffer
            else "accu op of onder 50%",
        }

    if solar > 300 and can_charge:
        return {
            "group_action": "laden",
            "suggested_watts": 0,
            "decision_reason": "netto zonopwek",
            "can_charge": True,
            "can_discharge": can_discharge,
            "charge_blocker": None,
            "discharge_blocker": None if can_discharge else "accu onder minimum",
        }
    if expensive is not None and price >= expensive and can_discharge:
        return {
            "group_action": "eigen gebruik",
            "suggested_watts": round(max_watts, 0),
            "decision_reason": "hoge prijs weinig zon",
            "can_charge": can_charge,
            "can_discharge": True,
            "charge_blocker": None if can_charge else "geen vrije accuruimte",
            "discharge_blocker": None,
        }
    return {
        "group_action": "stand-by",
        "suggested_watts": 0,
        "decision_reason": "geen actie nodig" if can_charge else "geen vrije accuruimte",
        "can_charge": can_charge,
        "can_discharge": can_discharge,
        "charge_blocker": None if can_charge else "geen vrije accuruimte",
        "discharge_blocker": None if can_discharge else "accu onder minimum",
    }


def best_scenario(
    scenarios: dict[str, dict[str, Any]],
    labels: dict[str, str],
) -> dict[str, Any]:
    """Return the scenario with the best live EUR/hour result."""
    best_key = ""
    best_data: dict[str, Any] = {}
    best_value = float("-inf")
    for key, data in scenarios.items():
        try:
            value = float(data.get("eur_per_hour") or 0)
        except (TypeError, ValueError):
            value = 0.0
        if value > best_value:
            best_key = key
            best_data = data
            best_value = value
    if not best_data:
        return {"label": "wachten"}
    return {
        "key": best_key,
        "label": best_data.get("label", labels.get(best_key, best_key)),
        "action": best_data.get("action"),
        "reason": best_data.get("reason"),
        "power_w": best_data.get("power_w"),
        "eur_per_hour": best_data.get("eur_per_hour"),
        "day_eur": best_data.get("day_eur"),
        "week_eur": best_data.get("week_eur"),
        "month_eur": best_data.get("month_eur"),
        "input_ready": best_data.get("input_ready"),
        "input_warnings": best_data.get("input_warnings"),
        "price_eur_kwh": best_data.get("price_eur_kwh"),
        "battery_soc": best_data.get("battery_soc"),
    }


def scenario_is_actionable(scenario: dict[str, Any]) -> bool:
    """Return whether a best-scenario result should start actual control."""
    if not scenario.get("key"):
        return False
    action = str(scenario.get("action") or "").lower()
    passive_actions = {"", "wachten", "stand-by", "buffer bewaken"}
    try:
        eur_per_hour = float(scenario.get("eur_per_hour") or 0)
    except (TypeError, ValueError):
        eur_per_hour = 0.0
    try:
        power_w = abs(float(scenario.get("power_w") or 0))
    except (TypeError, ValueError):
        power_w = 0.0
    if action in passive_actions and eur_per_hour <= 0 and power_w < 1:
        return False
    return True


def scenario_execution_state(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return a readable execution verdict for a scenario."""
    if not scenario:
        return {
            "state": "wacht",
            "summary": "wacht op scenario-data",
            "blocker": "scenario-data ontbreekt",
            "actionable": False,
        }
    warnings = scenario.get("input_warnings") or []
    if warnings:
        return {
            "state": "data nodig",
            "summary": f"data nodig: {warnings[0]}",
            "blocker": warnings[0],
            "actionable": False,
        }
    if scenario_is_actionable(scenario):
        action = scenario.get("action") or "actie"
        power = _as_float(scenario.get("power_w")) or 0
        return {
            "state": "uitvoerbaar",
            "summary": f"{action} ({power:.0f} W)",
            "blocker": None,
            "actionable": True,
        }
    return {
        "state": "wacht",
        "summary": scenario.get("reason") or "geen actie nodig",
        "blocker": "geen uitvoerbare actie",
        "actionable": False,
    }


def scenario_choice_summary(
    selected_strategy: str,
    selected_key: str | None,
    selected_data: dict[str, Any],
    best: dict[str, Any],
) -> dict[str, Any]:
    """Summarize the selected scenario versus the best advice."""
    best_key = best.get("key")
    selected_label = selected_data.get("label") if selected_key else "Uit"
    best_label = best.get("label") or "wachten"
    selected_eur = _as_float(selected_data.get("eur_per_hour")) or 0
    best_eur = _as_float(best.get("eur_per_hour")) or 0
    delta_eur = round(best_eur - selected_eur, 3)
    if selected_key is None:
        state = "uit"
        summary = f"uit; advies {best_label}"
    elif not best_key:
        state = "wachten"
        summary = f"{selected_label}: wacht op scenario-data"
    elif selected_key == best_key:
        state = "volgt advies"
        summary = f"{selected_label}: volgt advies"
    else:
        state = "wijkt af"
        summary = f"{selected_label} wijkt af van {best_label} ({delta_eur:+.2f} EUR/u)"
    return {
        "summary": summary,
        "state": state,
        "selected_strategy": selected_strategy,
        "selected_scenario_key": selected_key,
        "selected_label": selected_label,
        "selected_action": selected_data.get("action"),
        "selected_reason": selected_data.get("reason"),
        "selected_eur_per_hour": selected_data.get("eur_per_hour"),
        "best_scenario_key": best_key,
        "best_label": best_label,
        "best_action": best.get("action"),
        "best_reason": best.get("reason"),
        "best_eur_per_hour": best.get("eur_per_hour"),
        "delta_eur_per_hour": delta_eur,
    }


def next_powerstream_action(plan: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the first concrete PowerStream action for the dashboard flow."""
    if not plan:
        return {"summary": "geen PowerStreams", "action_type": "none"}

    item = next((entry for entry in plan if entry.get("strategy_error")), None)
    if item:
        return _next_action_attrs(
            item,
            "error",
            f"fout bij {item.get('name')}: {item.get('strategy_error')}",
        )

    item = next((entry for entry in plan if entry.get("strategy_throttled")), None)
    if item:
        wait = item.get("strategy_next_update_seconds")
        suffix = f" ({wait}s)" if wait is not None else ""
        return _next_action_attrs(item, "wait", f"wacht op {item.get('name')}{suffix}")

    item = next((entry for entry in plan if entry.get("command_needed")), None)
    if item:
        target = _as_float(item.get("suggested_watts")) or 0
        current = _as_float(item.get("current_watts"))
        if current is None:
            summary = f"zet {item.get('name')} naar {target:.0f} W"
        else:
            delta = float(item.get("delta_watts") or 0)
            summary = f"zet {item.get('name')} naar {target:.0f} W ({delta:+.0f} W)"
        return _next_action_attrs(item, "set_power", summary)

    item = next(
        (
            entry
            for entry in plan
            if entry.get("current_watts_verified") is False
            and not entry.get("command_needed")
        ),
        None,
    )
    if item:
        return _next_action_attrs(
            item,
            "wait",
            f"wacht op gemeten waarde van {item.get('name')}",
        )

    item = next(
        (
            entry
            for entry in plan
            if not entry.get("current_watts_known")
            and not entry.get("command_needed")
        ),
        None,
    )
    if item:
        return _next_action_attrs(
            item,
            "wait",
            f"wacht op actuele waarde van {item.get('name')}",
        )

    item = next(
        (entry for entry in plan if float(entry.get("suggested_watts") or 0) > 0),
        None,
    )
    if item:
        target = _as_float(item.get("suggested_watts")) or 0
        return _next_action_attrs(
            item, "hold", f"houd {item.get('name')} op {target:.0f} W"
        )

    return {
        "summary": "stand-by",
        "action_type": "standby",
        "group_count": len(plan),
    }


def next_dashboard_action(
    plan: list[dict[str, Any]],
    readiness: dict[str, Any],
    dry_run: bool,
    strategy: str,
) -> dict[str, Any]:
    """Return the next action, including whether control is allowed right now."""
    planned = next_powerstream_action(plan)
    if dry_run:
        return {
            **planned,
            "summary": f"testmodus: {planned.get('summary', 'stand-by')}",
            "action_type": "test_mode",
            "can_execute": False,
            "command_required": planned.get("action_type") == "set_power",
            "blocked_by": "test_mode",
        }
    if readiness.get("status") != "klaar":
        return {
            **planned,
            "summary": f"eerst: {readiness.get('next_step') or 'controleer datacheck'}",
            "action_type": "needs_data",
            "can_execute": False,
            "command_required": planned.get("action_type") == "set_power",
            "blocked_by": readiness.get("status"),
            "readiness_status": readiness.get("status"),
            "readiness_score": readiness.get("score"),
        }
    if strategy == "idle":
        return {
            **planned,
            "summary": "scenario uit",
            "action_type": "idle",
            "can_execute": False,
            "command_required": False,
            "blocked_by": "strategy_idle",
        }
    command_required = planned.get("action_type") == "set_power"
    return {
        **planned,
        "can_execute": command_required,
        "command_required": command_required,
        "blocked_by": None,
        "readiness_status": readiness.get("status"),
        "readiness_score": readiness.get("score"),
    }


def flow_snapshot_state(
    readiness: dict[str, Any], next_action: dict[str, Any], dry_run: bool
) -> str:
    """Return a short dashboard state for the simple flow snapshot."""
    action_type = next_action.get("action_type")
    if action_type == "error":
        return "fout"
    if readiness.get("status") == "actie nodig" or action_type == "needs_data":
        return "data nodig"
    if dry_run or action_type == "test_mode":
        return "testmodus"
    if action_type == "idle":
        return "scenario uit"
    if next_action.get("can_execute"):
        return "kan sturen"
    if action_type in {"wait", "none"}:
        return "wacht"
    return "stand-by"


def flow_snapshot_icon(snapshot_state: str) -> str:
    """Return an icon name for a simple flow snapshot state."""
    return {
        "kan sturen": "mdi:check-circle",
        "testmodus": "mdi:flask",
        "data nodig": "mdi:database-alert",
        "scenario uit": "mdi:pause-circle",
        "wacht": "mdi:timer-sand",
        "fout": "mdi:alert-circle",
        "stand-by": "mdi:power-standby",
    }.get(snapshot_state, "mdi:help-circle")


def flow_snapshot_phase(snapshot_state: str) -> str:
    """Return a compact phase name for a simple flow snapshot state."""
    return {
        "data nodig": "setup",
        "testmodus": "simuleren",
        "kan sturen": "sturen",
        "wacht": "wachten",
        "scenario uit": "uit",
        "fout": "fout",
        "stand-by": "stand-by",
    }.get(snapshot_state, "onbekend")


def flow_ready_state(
    readiness: dict[str, Any],
    best: dict[str, Any],
    choice: dict[str, Any],
    next_action: dict[str, Any],
    dry_run: bool,
    strategy: str,
) -> dict[str, Any]:
    """Return one visible verdict for whether the main flow is trustworthy."""
    actionable = scenario_is_actionable(best)
    if readiness.get("status") == "actie nodig":
        state = "actie nodig"
        reason = readiness.get("next_step") or "controleer datacheck"
        icon = "mdi:alert-circle"
    elif dry_run:
        state = "testmodus"
        reason = "sturing wordt gesimuleerd"
        icon = "mdi:flask"
    elif strategy == "idle":
        state = "uit"
        reason = "scenario staat uit"
        icon = "mdi:pause-circle"
    elif not actionable:
        state = "wachten"
        reason = best.get("reason") or "geen uitvoerbaar advies"
        icon = "mdi:timer-sand"
    elif choice.get("state") == "wijkt af":
        state = "afwijkend"
        reason = choice.get("summary")
        icon = "mdi:swap-horizontal"
    elif next_action.get("can_execute"):
        state = "klaar"
        reason = next_action.get("summary") or "kan sturen"
        icon = "mdi:check-circle"
    else:
        state = "stand-by"
        reason = next_action.get("summary") or "geen actie nodig"
        icon = "mdi:power-standby"
    return {
        "state": state,
        "reason": reason,
        "icon": icon,
        "best_actionable": actionable,
    }


def scenario_execution_hint(action: dict[str, Any]) -> str:
    """Summarize whether a visible scenario plan can be executed now."""
    if action.get("can_execute"):
        return "kan sturen"
    action_type = action.get("action_type")
    if action_type == "test_mode":
        return "testmodus"
    if action_type == "needs_data":
        return "data nodig"
    if action_type == "idle":
        return "scenario uit"
    if action_type in {"wait", "none", "standby"}:
        return "wacht"
    if action.get("blocked_by"):
        return f"blokkeert: {action.get('blocked_by')}"
    return "stand-by"


def _next_action_attrs(
    item: dict[str, Any], action_type: str, summary: str
) -> dict[str, Any]:
    return {
        "summary": summary,
        "action_type": action_type,
        "serial": item.get("serial"),
        "name": item.get("name"),
        "current_watts": item.get("current_watts"),
        "current_watts_known": item.get("current_watts_known"),
        "current_watts_source": item.get("current_watts_source"),
        "current_watts_verified": item.get("current_watts_verified"),
        "suggested_watts": item.get("suggested_watts"),
        "delta_watts": item.get("delta_watts"),
        "command_needed": item.get("command_needed"),
        "strategy": item.get("strategy"),
        "reason": item.get("reason"),
        "plan_source": item.get("plan_source"),
        "managed_battery_name": item.get("managed_battery_name"),
        "managed_battery_soc": item.get("managed_battery_soc"),
    }


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
