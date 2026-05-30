"""Tests for local scenario and PowerStream policy helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "ecoflow_energy_control"
    / "policy.py"
)
SPEC = importlib.util.spec_from_file_location("eec_policy", MODULE_PATH)
policy = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(policy)


class PowerStreamPolicyTest(unittest.TestCase):
    def test_trading_exports_on_expensive_power(self) -> None:
        decision = policy.powerstream_group_decision(
            "max_trading",
            {"max_watts": 600, "battery_soc": 65},
            0.42,
            {"cheap": 0.05, "expensive": 0.35},
            0,
        )
        self.assertEqual(decision["group_action"], "terugleveren")
        self.assertEqual(decision["suggested_watts"], 600)

    def test_trading_charges_on_cheap_sunny_power(self) -> None:
        decision = policy.powerstream_group_decision(
            "max_trading",
            {"max_watts": 600, "battery_soc": 65, "battery_free_wh": 2500},
            0.02,
            {"cheap": 0.05, "expensive": 0.35},
            900,
        )
        self.assertEqual(decision["group_action"], "laden")
        self.assertEqual(decision["suggested_watts"], 0)
        self.assertTrue(decision["can_charge"])

    def test_trading_does_not_charge_when_battery_full(self) -> None:
        decision = policy.powerstream_group_decision(
            "max_trading",
            {"max_watts": 600, "battery_soc": 99, "battery_free_wh": 0},
            0.02,
            {"cheap": 0.05, "expensive": 0.35},
            900,
        )
        self.assertEqual(decision["group_action"], "wachten")
        self.assertFalse(decision["can_charge"])
        self.assertEqual(decision["charge_blocker"], "geen vrije accuruimte")

    def test_self_use_does_not_export_when_battery_low(self) -> None:
        decision = policy.powerstream_group_decision(
            "max_self_use",
            {"max_watts": 600, "battery_soc": 15},
            0.42,
            {"cheap": 0.05, "expensive": 0.35},
            0,
        )
        self.assertEqual(decision["group_action"], "stand-by")
        self.assertEqual(decision["suggested_watts"], 0)

    def test_buffer_50_exports_only_above_buffer(self) -> None:
        decision = policy.powerstream_group_decision(
            "buffer_50",
            {"max_watts": 600, "battery_soc": 58},
            0.42,
            {"cheap": 0.05, "expensive": 0.35},
            0,
        )
        self.assertEqual(decision["group_action"], "terugleveren boven buffer")
        self.assertEqual(decision["suggested_watts"], 600)

        blocked = policy.powerstream_group_decision(
            "buffer_50",
            {"max_watts": 600, "battery_soc": 48},
            0.42,
            {"cheap": 0.05, "expensive": 0.35},
            0,
        )
        self.assertEqual(blocked["group_action"], "buffer bewaken")
        self.assertEqual(blocked["suggested_watts"], 0)


class BestScenarioPolicyTest(unittest.TestCase):
    def test_best_scenario_uses_highest_eur_per_hour(self) -> None:
        best = policy.best_scenario(
            {
                "self_use": {"label": "Eigen", "eur_per_hour": 0.08},
                "trading": {
                    "label": "Handelen",
                    "eur_per_hour": 0.31,
                    "reason": "hoge prijs",
                    "input_ready": False,
                    "input_warnings": ["accu-SoC onbekend"],
                    "price_eur_kwh": 0.42,
                    "battery_soc": None,
                },
                "buffer_50": {"label": "Buffer", "eur_per_hour": 0.12},
            },
            {},
        )
        self.assertEqual(best["key"], "trading")
        self.assertEqual(best["label"], "Handelen")
        self.assertEqual(best["reason"], "hoge prijs")
        self.assertFalse(best["input_ready"])
        self.assertEqual(best["input_warnings"], ["accu-SoC onbekend"])
        self.assertEqual(best["price_eur_kwh"], 0.42)
        self.assertIsNone(best["battery_soc"])

    def test_passive_best_scenario_is_not_actionable(self) -> None:
        self.assertFalse(
            policy.scenario_is_actionable(
                {
                    "key": "trading",
                    "action": "wachten",
                    "eur_per_hour": 0,
                    "power_w": 0,
                }
            )
        )
        self.assertFalse(
            policy.scenario_is_actionable(
                {
                    "key": "self_use",
                    "action": "stand-by",
                    "eur_per_hour": 0,
                    "power_w": 0,
                }
            )
        )

    def test_active_best_scenario_is_actionable(self) -> None:
        self.assertTrue(
            policy.scenario_is_actionable(
                {
                    "key": "trading",
                    "action": "terugleveren",
                    "eur_per_hour": 0.31,
                    "power_w": 600,
                }
            )
        )

    def test_scenario_execution_state_explains_actionability(self) -> None:
        executable = policy.scenario_execution_state(
            {
                "key": "trading",
                "action": "terugleveren",
                "eur_per_hour": 0.31,
                "power_w": 600,
                "input_warnings": [],
            }
        )
        self.assertEqual(executable["state"], "uitvoerbaar")
        self.assertEqual(executable["summary"], "terugleveren (600 W)")
        self.assertTrue(executable["actionable"])

        waiting = policy.scenario_execution_state(
            {
                "key": "self_use",
                "action": "stand-by",
                "eur_per_hour": 0,
                "power_w": 0,
                "reason": "geen bruikbare zonopwek",
                "input_warnings": [],
            }
        )
        self.assertEqual(waiting["state"], "wacht")
        self.assertEqual(waiting["blocker"], "geen uitvoerbare actie")

        missing_data = policy.scenario_execution_state(
            {"input_warnings": ["accu-SoC onbekend"]}
        )
        self.assertEqual(missing_data["state"], "data nodig")
        self.assertEqual(missing_data["blocker"], "accu-SoC onbekend")


class ScenarioChoiceSummaryPolicyTest(unittest.TestCase):
    def test_choice_summary_shows_idle_strategy(self) -> None:
        summary = policy.scenario_choice_summary(
            "idle",
            None,
            {},
            {"key": "trading", "label": "Handelen", "eur_per_hour": 0.42},
        )
        self.assertEqual(summary["state"], "uit")
        self.assertEqual(summary["summary"], "uit; advies Handelen")
        self.assertEqual(summary["selected_label"], "Uit")

    def test_choice_summary_waits_without_best_scenario(self) -> None:
        summary = policy.scenario_choice_summary(
            "max_self_use",
            "self_use",
            {"label": "Eigen gebruik", "eur_per_hour": 0.11},
            {"label": "wachten"},
        )
        self.assertEqual(summary["state"], "wachten")
        self.assertEqual(summary["summary"], "Eigen gebruik: wacht op scenario-data")

    def test_choice_summary_follows_best_scenario(self) -> None:
        summary = policy.scenario_choice_summary(
            "max_trading",
            "trading",
            {"label": "Handelen", "eur_per_hour": 0.31},
            {"key": "trading", "label": "Handelen", "eur_per_hour": 0.31},
        )
        self.assertEqual(summary["state"], "volgt advies")
        self.assertEqual(summary["summary"], "Handelen: volgt advies")
        self.assertEqual(summary["delta_eur_per_hour"], 0)

    def test_choice_summary_reports_difference_when_choice_deviates(self) -> None:
        summary = policy.scenario_choice_summary(
            "max_self_use",
            "self_use",
            {"label": "Eigen gebruik", "eur_per_hour": 0.08},
            {"key": "trading", "label": "Handelen", "eur_per_hour": 0.31},
        )
        self.assertEqual(summary["state"], "wijkt af")
        self.assertEqual(
            summary["summary"], "Eigen gebruik wijkt af van Handelen (+0.23 EUR/u)"
        )
        self.assertEqual(summary["delta_eur_per_hour"], 0.23)


class NextPowerStreamActionPolicyTest(unittest.TestCase):
    def test_next_action_reports_no_powerstreams(self) -> None:
        action = policy.next_powerstream_action([])
        self.assertEqual(action["action_type"], "none")
        self.assertEqual(action["summary"], "geen PowerStreams")

    def test_next_action_prioritizes_errors(self) -> None:
        action = policy.next_powerstream_action(
            [
                {
                    "name": "PowerStream A",
                    "command_needed": True,
                    "suggested_watts": 300,
                    "delta_watts": 300,
                },
                {"name": "PowerStream B", "strategy_error": "API 1008"},
            ]
        )
        self.assertEqual(action["action_type"], "error")
        self.assertEqual(action["name"], "PowerStream B")
        self.assertIn("API 1008", action["summary"])

    def test_next_action_waits_for_throttle_before_new_command(self) -> None:
        action = policy.next_powerstream_action(
            [
                {
                    "name": "PowerStream A",
                    "strategy_throttled": True,
                    "strategy_next_update_seconds": 42,
                },
                {
                    "name": "PowerStream B",
                    "command_needed": True,
                    "suggested_watts": 500,
                    "delta_watts": 200,
                },
            ]
        )
        self.assertEqual(action["action_type"], "wait")
        self.assertEqual(action["summary"], "wacht op PowerStream A (42s)")

    def test_next_action_sets_power_with_delta_when_current_is_known(self) -> None:
        action = policy.next_powerstream_action(
            [
                {
                    "name": "PowerStream A",
                    "current_watts": 200,
                    "current_watts_known": True,
                    "suggested_watts": 600,
                    "delta_watts": 400,
                    "command_needed": True,
                }
            ]
        )
        self.assertEqual(action["action_type"], "set_power")
        self.assertEqual(action["summary"], "zet PowerStream A naar 600 W (+400 W)")

    def test_next_action_sets_power_without_delta_when_current_is_unknown(self) -> None:
        action = policy.next_powerstream_action(
            [
                {
                    "name": "PowerStream A",
                    "current_watts": None,
                    "current_watts_known": False,
                    "suggested_watts": 600,
                    "delta_watts": 600,
                    "command_needed": True,
                }
            ]
        )
        self.assertEqual(action["action_type"], "set_power")
        self.assertEqual(action["summary"], "zet PowerStream A naar 600 W")

    def test_next_action_waits_when_current_value_is_missing(self) -> None:
        action = policy.next_powerstream_action(
            [
                {
                    "name": "PowerStream A",
                    "current_watts": None,
                    "current_watts_known": False,
                    "suggested_watts": 0,
                    "command_needed": False,
                }
            ]
        )
        self.assertEqual(action["action_type"], "wait")
        self.assertEqual(action["summary"], "wacht op actuele waarde van PowerStream A")

    def test_next_action_holds_active_target_or_standby(self) -> None:
        hold = policy.next_powerstream_action(
            [
                {
                    "name": "PowerStream A",
                    "current_watts": 600,
                    "current_watts_known": True,
                    "suggested_watts": 600,
                    "command_needed": False,
                }
            ]
        )
        self.assertEqual(hold["action_type"], "hold")
        self.assertEqual(hold["summary"], "houd PowerStream A op 600 W")

        standby = policy.next_powerstream_action(
            [
                {
                    "name": "PowerStream A",
                    "current_watts": 0,
                    "current_watts_known": True,
                    "suggested_watts": 0,
                    "command_needed": False,
                }
            ]
        )
        self.assertEqual(standby["action_type"], "standby")
        self.assertEqual(standby["summary"], "stand-by")

    def test_next_action_waits_when_current_power_is_not_telemetry_verified(self) -> None:
        action = policy.next_powerstream_action(
            [
                {
                    "name": "PowerStream A",
                    "current_watts": 600,
                    "current_watts_known": True,
                    "current_watts_verified": False,
                    "current_watts_source": "stored_target",
                    "suggested_watts": 600,
                    "command_needed": False,
                }
            ]
        )
        self.assertEqual(action["action_type"], "wait")
        self.assertEqual(action["summary"], "wacht op gemeten waarde van PowerStream A")
        self.assertFalse(action["current_watts_verified"])
        self.assertEqual(action["current_watts_source"], "stored_target")


class NextDashboardActionPolicyTest(unittest.TestCase):
    def _plan(self) -> list[dict[str, object]]:
        return [
            {
                "name": "PowerStream A",
                "current_watts": 200,
                "current_watts_known": True,
                "suggested_watts": 600,
                "delta_watts": 400,
                "command_needed": True,
            }
        ]

    def test_dashboard_action_shows_test_mode_before_command(self) -> None:
        action = policy.next_dashboard_action(
            self._plan(),
            {"status": "klaar", "score": 100},
            True,
            "max_self_use",
        )
        self.assertEqual(action["action_type"], "test_mode")
        self.assertFalse(action["can_execute"])
        self.assertTrue(action["command_required"])
        self.assertEqual(action["blocked_by"], "test_mode")
        self.assertEqual(
            action["summary"], "testmodus: zet PowerStream A naar 600 W (+400 W)"
        )

    def test_dashboard_action_requires_ready_data_before_command(self) -> None:
        action = policy.next_dashboard_action(
            self._plan(),
            {
                "status": "gedeeltelijk",
                "score": 71,
                "next_step": "controleer PowerStream-data",
            },
            False,
            "max_self_use",
        )
        self.assertEqual(action["action_type"], "needs_data")
        self.assertFalse(action["can_execute"])
        self.assertTrue(action["command_required"])
        self.assertEqual(action["blocked_by"], "gedeeltelijk")
        self.assertEqual(action["summary"], "eerst: controleer PowerStream-data")

    def test_dashboard_action_shows_strategy_idle_before_command(self) -> None:
        action = policy.next_dashboard_action(
            self._plan(),
            {"status": "klaar", "score": 100},
            False,
            "idle",
        )
        self.assertEqual(action["action_type"], "idle")
        self.assertFalse(action["can_execute"])
        self.assertFalse(action["command_required"])
        self.assertEqual(action["blocked_by"], "strategy_idle")
        self.assertEqual(action["summary"], "scenario uit")

    def test_dashboard_action_allows_ready_command(self) -> None:
        action = policy.next_dashboard_action(
            self._plan(),
            {"status": "klaar", "score": 100},
            False,
            "max_self_use",
        )
        self.assertEqual(action["action_type"], "set_power")
        self.assertTrue(action["can_execute"])
        self.assertTrue(action["command_required"])
        self.assertIsNone(action["blocked_by"])

    def test_dashboard_action_does_not_call_hold_or_standby_executable(self) -> None:
        hold = policy.next_dashboard_action(
            [
                {
                    "name": "PowerStream A",
                    "current_watts": 600,
                    "current_watts_known": True,
                    "suggested_watts": 600,
                    "command_needed": False,
                }
            ],
            {"status": "klaar", "score": 100},
            False,
            "max_trading",
        )
        self.assertEqual(hold["action_type"], "hold")
        self.assertFalse(hold["can_execute"])
        self.assertFalse(hold["command_required"])

        standby = policy.next_dashboard_action(
            [
                {
                    "name": "PowerStream A",
                    "current_watts": 0,
                    "current_watts_known": True,
                    "suggested_watts": 0,
                    "command_needed": False,
                }
            ],
            {"status": "klaar", "score": 100},
            False,
            "max_trading",
        )
        self.assertEqual(standby["action_type"], "standby")
        self.assertFalse(standby["can_execute"])
        self.assertFalse(standby["command_required"])

    def test_scenario_execution_hint_covers_visible_plan_prefixes(self) -> None:
        cases = (
            ({"can_execute": True, "action_type": "set_power"}, "kan sturen"),
            ({"can_execute": False, "action_type": "test_mode"}, "testmodus"),
            ({"can_execute": False, "action_type": "needs_data"}, "data nodig"),
            ({"can_execute": False, "action_type": "idle"}, "scenario uit"),
            ({"can_execute": False, "action_type": "wait"}, "wacht"),
            ({"can_execute": False, "blocked_by": "gedeeltelijk"}, "blokkeert: gedeeltelijk"),
            ({"can_execute": False, "action_type": "hold"}, "stand-by"),
        )
        for action, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(policy.scenario_execution_hint(action), expected)


class FlowSnapshotPolicyTest(unittest.TestCase):
    def test_flow_snapshot_state_covers_all_dashboard_phases(self) -> None:
        cases = (
            (
                "fout",
                {"status": "klaar"},
                {"action_type": "error"},
                False,
                "mdi:alert-circle",
                "fout",
            ),
            (
                "data nodig",
                {"status": "actie nodig"},
                {"action_type": "standby"},
                False,
                "mdi:database-alert",
                "setup",
            ),
            (
                "testmodus",
                {"status": "klaar"},
                {"action_type": "set_power"},
                True,
                "mdi:flask",
                "simuleren",
            ),
            (
                "scenario uit",
                {"status": "klaar"},
                {"action_type": "idle"},
                False,
                "mdi:pause-circle",
                "uit",
            ),
            (
                "kan sturen",
                {"status": "klaar"},
                {"action_type": "set_power", "can_execute": True},
                False,
                "mdi:check-circle",
                "sturen",
            ),
            (
                "wacht",
                {"status": "klaar"},
                {"action_type": "wait"},
                False,
                "mdi:timer-sand",
                "wachten",
            ),
            (
                "stand-by",
                {"status": "klaar"},
                {"action_type": "standby", "can_execute": False},
                False,
                "mdi:power-standby",
                "stand-by",
            ),
        )
        for state, readiness, action, dry_run, icon, phase in cases:
            with self.subTest(state=state):
                result = policy.flow_snapshot_state(readiness, action, dry_run)
                self.assertEqual(result, state)
                self.assertEqual(policy.flow_snapshot_icon(result), icon)
                self.assertEqual(policy.flow_snapshot_phase(result), phase)


class FlowReadyPolicyTest(unittest.TestCase):
    def test_flow_ready_state_covers_visible_verdicts(self) -> None:
        ready = {"status": "klaar", "score": 100}
        active_best = {
            "key": "trading",
            "action": "terugleveren",
            "power_w": 600,
            "eur_per_hour": 0.22,
            "reason": "hoge prijs",
        }
        waiting_best = {
            "key": "trading",
            "action": "wachten",
            "power_w": 0,
            "eur_per_hour": 0,
            "reason": "geen handelsmoment",
        }
        cases = (
            (
                "actie nodig",
                {"status": "actie nodig", "next_step": "controleer prijzen"},
                active_best,
                {"state": "volgt advies"},
                {"can_execute": True, "summary": "kan sturen"},
                False,
                "max_trading",
                "mdi:alert-circle",
            ),
            (
                "testmodus",
                ready,
                active_best,
                {"state": "volgt advies"},
                {"can_execute": True, "summary": "kan sturen"},
                True,
                "max_trading",
                "mdi:flask",
            ),
            (
                "uit",
                ready,
                active_best,
                {"state": "uit"},
                {"can_execute": False, "summary": "scenario uit"},
                False,
                "idle",
                "mdi:pause-circle",
            ),
            (
                "wachten",
                ready,
                waiting_best,
                {"state": "volgt advies"},
                {"can_execute": False, "summary": "wacht"},
                False,
                "max_trading",
                "mdi:timer-sand",
            ),
            (
                "afwijkend",
                ready,
                active_best,
                {"state": "wijkt af", "summary": "Eigen gebruik wijkt af"},
                {"can_execute": True, "summary": "kan sturen"},
                False,
                "max_self_use",
                "mdi:swap-horizontal",
            ),
            (
                "klaar",
                ready,
                active_best,
                {"state": "volgt advies"},
                {"can_execute": True, "summary": "kan sturen"},
                False,
                "max_trading",
                "mdi:check-circle",
            ),
            (
                "stand-by",
                ready,
                active_best,
                {"state": "volgt advies"},
                {"can_execute": False, "summary": "geen actie"},
                False,
                "max_trading",
                "mdi:power-standby",
            ),
        )
        for state, readiness, best, choice, action, dry_run, strategy, icon in cases:
            with self.subTest(state=state):
                result = policy.flow_ready_state(
                    readiness, best, choice, action, dry_run, strategy
                )
                self.assertEqual(result["state"], state)
                self.assertEqual(result["icon"], icon)
                self.assertIn("best_actionable", result)


if __name__ == "__main__":
    unittest.main()
