"""Tests for dashboard readiness checks."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "ecoflow_energy_control"
    / "health.py"
)
SPEC = importlib.util.spec_from_file_location("eec_health", MODULE_PATH)
health = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(health)


class DashboardReadinessTest(unittest.TestCase):
    def test_ready_when_core_data_is_available(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    }
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "klaar")
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["next_step"], "klaar voor sturen")
        self.assertTrue(result["insight_ready"])
        self.assertTrue(result["control_ready"])
        self.assertEqual(result["insight_status"], "basis klaar")
        self.assertEqual(result["insight_next_step"], "basisinzicht klaar")
        self.assertEqual(result["insight_checks"], ["prices", "batteries"])
        checks = {item["key"]: item for item in result["checks"]}
        self.assertEqual(checks["prices"]["details"]["price_hours"], 24)
        self.assertEqual(checks["prices"]["details"]["chart_hours"], 24)
        self.assertEqual(checks["batteries"]["details"]["configured"], 1)
        self.assertEqual(checks["batteries"]["details"]["live"], 1)
        self.assertEqual(checks["batteries"]["details"]["with_soc"], 1)
        self.assertEqual(checks["batteries"]["details"]["missing_soc"], 0)
        self.assertEqual(checks["powerstreams"]["details"]["live"], 1)
        self.assertEqual(
            checks["solar"]["details"]["corrected_solar_power"], 250
        )
        self.assertEqual(checks["weather"]["details"]["weather_label"], "zon")
        self.assertEqual(checks["scenarios"]["details"]["scenario_count"], 3)
        self.assertFalse(checks["execution"]["details"]["dry_run"])

    def test_source_summary_reports_all_clear(self) -> None:
        summary = health.source_summary(
            {
                "status": "klaar",
                "score": 100,
                "next_step": "klaar voor sturen",
                "blocking": [],
                "warnings": [],
                "checks": [
                    {"key": "prices", "status": "klaar", "message": "24 prijsuren"},
                    {"key": "batteries", "status": "klaar", "message": "1 batterij"},
                ],
            }
        )
        self.assertEqual(summary["summary"], "alle bronnen ok (2/2)")
        self.assertEqual(summary["ready_sources"], 2)
        self.assertEqual(summary["total_sources"], 2)
        self.assertIsNone(summary["first_issue_key"])

    def test_source_summary_prioritizes_blocking_issue(self) -> None:
        summary = health.source_summary(
            {
                "status": "actie nodig",
                "score": 50,
                "next_step": "haal prijsdata op",
                "blocking": ["prices"],
                "warnings": ["weather"],
                "checks": [
                    {
                        "key": "prices",
                        "status": "actie nodig",
                        "message": "geen actuele prijs",
                    },
                    {
                        "key": "weather",
                        "status": "gedeeltelijk",
                        "message": "geen uurverwachting",
                    },
                ],
            }
        )
        self.assertEqual(summary["summary"], "prijzen: geen actuele prijs")
        self.assertEqual(summary["first_issue_key"], "prices")
        self.assertEqual(summary["first_issue_label"], "prijzen")
        self.assertEqual(summary["first_issue_status"], "actie nodig")
        self.assertEqual(summary["first_issue_message"], "geen actuele prijs")

    def test_source_summary_uses_warning_when_no_blocker_exists(self) -> None:
        summary = health.source_summary(
            {
                "status": "gedeeltelijk",
                "score": 86,
                "next_step": "controleer weerdata",
                "blocking": [],
                "warnings": ["weather"],
                "checks": [
                    {"key": "prices", "status": "klaar", "message": "24 prijsuren"},
                    {
                        "key": "weather",
                        "status": "gedeeltelijk",
                        "message": "geen uurverwachting",
                    },
                ],
            }
        )
        self.assertEqual(summary["summary"], "weer: geen uurverwachting")
        self.assertEqual(summary["first_issue_label"], "weer")
        self.assertEqual(summary["first_issue_status"], "gedeeltelijk")
        self.assertEqual(summary["ready_sources"], 1)
        self.assertEqual(summary["total_sources"], 2)

    def test_source_summary_handles_empty_checks(self) -> None:
        summary = health.source_summary(
            {
                "status": "onbekend",
                "score": None,
                "next_step": None,
                "blocking": [],
                "warnings": [],
                "checks": [],
            }
        )
        self.assertEqual(summary["summary"], "geen bronchecks")
        self.assertEqual(summary["ready_sources"], 0)
        self.assertEqual(summary["total_sources"], 0)

    def test_live_missing_summary_uses_first_missing_source(self) -> None:
        summary = health.live_missing_summary(
            {
                "first_missing_label": "PowerStreams",
                "first_missing_message": "geen live vermogen",
            },
            "controleer Datacheck",
        )
        self.assertEqual(summary, "PowerStreams: geen live vermogen")

    def test_live_missing_summary_falls_back_without_source_message(self) -> None:
        self.assertEqual(
            health.live_missing_summary({}, "7/8 databronnen klaar"),
            "7/8 databronnen klaar",
        )
        self.assertEqual(
            health.live_missing_summary({}, None),
            "controleer Datacheck",
        )

    def test_next_user_step_prioritizes_minimal_setup(self) -> None:
        step = health.next_user_step(
            {"status": "actie nodig", "next_step": "haal prijsdata op"},
            {
                "ready_for_basic_insight": False,
                "next_step": "batterij toevoegen",
                "state": "actie nodig",
                "progress": 0,
            },
            {},
            dry_run=True,
        )
        self.assertEqual(step["state"], "basis nodig")
        self.assertEqual(step["summary"], "batterij toevoegen")
        self.assertEqual(step["category"], "setup")

    def test_next_user_step_turns_minimal_insight_into_control_advice(self) -> None:
        step = health.next_user_step(
            {
                "status": "gedeeltelijk",
                "score": 60,
                "next_step": "controleer PowerStream koppeling",
                "insight_ready": True,
                "control_ready": False,
            },
            {
                "ready_for_basic_insight": True,
                "ready_for_powerstream_control": False,
                "ready_for_full_optimization": False,
                "next_step": "PowerStream toevoegen",
                "state": "basis klaar",
                "progress": 60,
            },
            {},
            dry_run=True,
        )
        self.assertEqual(step["state"], "basis klaar")
        self.assertEqual(
            step["summary"], "PowerStream toevoegen voor automatische sturing"
        )
        self.assertTrue(step["insight_ready"])
        self.assertFalse(step["control_ready"])

    def test_next_user_step_prefers_testmode_before_real_control(self) -> None:
        step = health.next_user_step(
            {
                "status": "klaar",
                "score": 100,
                "next_step": "klaar voor sturen",
                "insight_ready": True,
                "control_ready": True,
            },
            {
                "ready_for_basic_insight": True,
                "ready_for_powerstream_control": True,
                "ready_for_full_optimization": True,
                "next_step": "basisconfiguratie compleet",
                "state": "compleet",
                "progress": 100,
            },
            {"can_execute": True, "summary": "PowerStream naar 600 W"},
            dry_run=True,
        )
        self.assertEqual(step["state"], "testmodus")
        self.assertEqual(step["summary"], "zet testmodus uit om echt te sturen")

    def test_next_user_step_uses_live_missing_source_for_action_needed(self) -> None:
        step = health.next_user_step(
            {
                "status": "actie nodig",
                "score": 50,
                "next_step": "controleer PowerStream koppeling",
                "insight_ready": True,
                "control_ready": False,
            },
            {
                "ready_for_basic_insight": True,
                "ready_for_powerstream_control": True,
                "ready_for_full_optimization": True,
            },
            {},
            dry_run=False,
            live_proof={
                "first_missing_label": "PowerStreams",
                "first_missing_message": "geen live vermogen",
            },
        )
        self.assertEqual(step["state"], "actie nodig")
        self.assertEqual(step["summary"], "PowerStreams: geen live vermogen")

    def test_next_user_step_points_to_advice_when_executable(self) -> None:
        step = health.next_user_step(
            {
                "status": "klaar",
                "score": 100,
                "next_step": "klaar voor sturen",
                "insight_ready": True,
                "control_ready": True,
            },
            {
                "ready_for_basic_insight": True,
                "ready_for_powerstream_control": True,
                "ready_for_full_optimization": True,
                "next_step": "basisconfiguratie compleet",
                "state": "compleet",
                "progress": 100,
            },
            {"can_execute": True, "summary": "PowerStream naar 600 W"},
            dry_run=False,
        )
        self.assertEqual(step["state"], "startbaar")
        self.assertEqual(step["summary"], "druk Advies: PowerStream naar 600 W")
        self.assertEqual(step["category"], "control")

    def test_simple_flow_stage_names_minimal_insight(self) -> None:
        stage = health.simple_flow_stage(
            {
                "status": "gedeeltelijk",
                "score": 60,
                "next_step": "controleer PowerStream koppeling",
                "insight_ready": True,
                "control_ready": False,
            },
            {
                "ready_for_basic_insight": True,
                "ready_for_powerstream_control": False,
                "ready_for_full_optimization": False,
                "next_step": "PowerStream toevoegen",
                "state": "basis klaar",
                "progress": 60,
            },
            {},
            dry_run=True,
        )
        self.assertEqual(stage["state"], "inzicht klaar")
        self.assertEqual(stage["category"], "insight")
        self.assertIn("PowerStream toevoegen", stage["summary"])
        self.assertTrue(stage["insight_ready"])
        self.assertFalse(stage["control_ready"])

    def test_simple_flow_stage_marks_testmode_after_live_control_ready(self) -> None:
        stage = health.simple_flow_stage(
            {
                "status": "klaar",
                "score": 100,
                "next_step": "klaar voor sturen",
                "insight_ready": True,
                "control_ready": True,
            },
            {
                "ready_for_basic_insight": True,
                "ready_for_powerstream_control": True,
                "ready_for_full_optimization": True,
                "next_step": "basisconfiguratie compleet",
                "state": "compleet",
                "progress": 100,
            },
            {"can_execute": True, "summary": "PowerStream naar 600 W"},
            dry_run=True,
        )
        self.assertEqual(stage["state"], "testmodus")
        self.assertEqual(stage["category"], "control")
        self.assertTrue(stage["dry_run"])

    def test_simple_flow_stage_marks_executable_control_as_startable(self) -> None:
        stage = health.simple_flow_stage(
            {
                "status": "klaar",
                "score": 100,
                "next_step": "klaar voor sturen",
                "insight_ready": True,
                "control_ready": True,
            },
            {
                "ready_for_basic_insight": True,
                "ready_for_powerstream_control": True,
                "ready_for_full_optimization": True,
                "next_step": "basisconfiguratie compleet",
                "state": "compleet",
                "progress": 100,
            },
            {"can_execute": True, "summary": "PowerStream naar 600 W"},
            dry_run=False,
        )
        self.assertEqual(stage["state"], "startbaar")
        self.assertEqual(stage["summary"], "Advies: PowerStream naar 600 W")
        self.assertTrue(stage["can_execute"])

    def test_setup_state_marks_missing_required_basics(self) -> None:
        setup = health.setup_state({}, dry_run=True)
        self.assertEqual(setup["state"], "actie nodig")
        self.assertEqual(setup["current_capability"], "nog geen basisinzicht")
        self.assertEqual(setup["next_step"], "batterij toevoegen")
        self.assertEqual(setup["progress"], 0)
        self.assertEqual(setup["next_step_kind"], "verplicht")
        self.assertFalse(setup["ready_for_basic_insight"])
        self.assertFalse(setup["ready_for_powerstream_control"])
        self.assertFalse(setup["ready_for_full_optimization"])
        self.assertEqual(
            setup["missing_required"],
            ["batterij toevoegen"],
        )
        self.assertEqual(setup["price_source"], "energyzero")
        self.assertTrue(setup["price_source_defaulted"])
        self.assertEqual(setup["required_total"], 1)

    def test_setup_state_scores_minimal_setup_as_basis_ready(self) -> None:
        setup = health.setup_state(
            {
                "batteries": [{"serial": "bat"}],
                "price_source": "energyzero",
            },
            dry_run=True,
        )
        self.assertEqual(setup["state"], "basis klaar")
        self.assertEqual(setup["current_capability"], "basisinzicht beschikbaar")
        self.assertEqual(setup["progress"], 60)
        self.assertEqual(setup["required_done"], 1)
        self.assertEqual(setup["required_total"], 1)
        self.assertEqual(setup["optional_done"], 0)
        self.assertEqual(setup["next_step"], "PowerStream toevoegen")
        self.assertEqual(setup["next_step_kind"], "aanbevolen")
        self.assertTrue(setup["ready_for_basic_insight"])
        self.assertFalse(setup["ready_for_powerstream_control"])
        self.assertFalse(setup["ready_for_full_optimization"])

    def test_setup_state_defaults_price_source_for_minimal_setup(self) -> None:
        setup = health.setup_state(
            {
                "batteries": [{"serial": "bat"}],
            },
            dry_run=True,
        )
        self.assertEqual(setup["state"], "basis klaar")
        self.assertEqual(setup["price_source"], "energyzero")
        self.assertTrue(setup["price_source_defaulted"])
        self.assertTrue(setup["ready_for_basic_insight"])
        self.assertEqual(setup["missing_required"], [])
        self.assertEqual(setup["basic_requirements"], ["batterij"])

    def test_setup_state_scores_complete_setup(self) -> None:
        setup = health.setup_state(
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "price_source": "energyzero",
                "weather_city": "Amsterdam",
            },
            dry_run=False,
        )
        self.assertEqual(setup["state"], "compleet")
        self.assertEqual(setup["current_capability"], "volledige optimalisatie beschikbaar")
        self.assertEqual(setup["progress"], 100)
        self.assertEqual(setup["next_step"], "basisconfiguratie compleet")
        self.assertEqual(setup["next_step_kind"], "klaar")
        self.assertEqual(setup["basic_requirements"], ["batterij"])
        self.assertEqual(setup["control_requirements"], ["PowerStream"])
        self.assertEqual(setup["optimization_requirements"], ["zonmeter", "weerstad"])
        self.assertTrue(setup["ready_for_basic_insight"])
        self.assertTrue(setup["ready_for_powerstream_control"])
        self.assertTrue(setup["ready_for_full_optimization"])
        self.assertFalse(setup["dry_run"])

    def test_action_needed_when_battery_and_prices_are_missing(self) -> None:
        result = health.dashboard_readiness(
            {"scenarios": {}},
            {"batteries": [{"serial": "bat"}], "powerstreams": [], "dry_run": False},
        )
        self.assertEqual(result["status"], "actie nodig")
        self.assertFalse(result["insight_ready"])
        self.assertFalse(result["control_ready"])
        self.assertEqual(result["insight_status"], "actie nodig")
        self.assertIn("prices", result["blocking"])
        self.assertIn("batteries", result["blocking"])
        self.assertEqual(result["next_step"], "haal prijsdata op: geen actuele prijs")

    def test_optional_sources_make_partial_status(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {},
                "corrected_solar_power": 0,
                "weather": {},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {"batteries": [{"serial": "bat"}], "powerstreams": [], "dry_run": False},
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        self.assertTrue(result["insight_ready"])
        self.assertFalse(result["control_ready"])
        self.assertEqual(result["insight_next_step"], "basisinzicht klaar")
        self.assertIn("powerstreams", result["warnings"])
        self.assertIn("weather", result["warnings"])
        self.assertEqual(
            result["next_step"],
            "controleer PowerStream koppeling: geen PowerStreams ingesteld",
        )

    def test_homewizard_p1_history_is_ready_when_statistics_exist(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    }
                },
                "corrected_solar_power": 250,
                "homewizard_meters": {
                    "P1": {
                        "history": {
                            "available": True,
                            "periods": {
                                "today": {"net_import_kwh": 2.1},
                                "week": {"net_import_kwh": 14.3},
                                "month": {"net_import_kwh": 61.2},
                            },
                        }
                    }
                },
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [
                    {"name": "P1", "role": "grid_meter", "source": "homeassistant"}
                ],
                "dry_run": False,
            },
        )
        checks = {item["key"]: item for item in result["checks"]}
        self.assertEqual(checks["p1_history"]["status"], "klaar")
        self.assertEqual(checks["p1_history"]["details"]["with_history"], 1)
        self.assertEqual(result["status"], "klaar")

    def test_missing_homewizard_p1_history_is_visible_warning(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    }
                },
                "corrected_solar_power": 250,
                "homewizard_meters": {"P1": {"history": {"available": False}}},
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [
                    {"name": "P1", "role": "grid_meter", "source": "homeassistant"}
                ],
                "dry_run": False,
            },
        )
        checks = {item["key"]: item for item in result["checks"]}
        self.assertEqual(checks["p1_history"]["status"], "gedeeltelijk")
        self.assertIn("p1_history", result["warnings"])
        self.assertEqual(
            result["next_step"],
            "controleer P1 historie: P1-historie ontbreekt",
        )

    def test_dry_run_keeps_dashboard_partially_ready(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    }
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": True,
            },
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        self.assertIn("execution", result["warnings"])
        self.assertEqual(result["next_step"], "zet testmodus uit: testmodus staat aan")

    def test_missing_price_chart_keeps_dashboard_partially_ready(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": []},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    }
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        self.assertIn("prices", result["warnings"])
        self.assertEqual(
            result["next_step"],
            "haal prijsdata op: prijsgrafiek mist komende uren",
        )

    def test_short_price_chart_keeps_dashboard_partially_ready(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 6},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    }
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        self.assertIn("prices", result["warnings"])
        self.assertEqual(
            result["next_step"],
            "haal prijsdata op: prijsgrafiek heeft minder dan 12 uur",
        )

    def test_powerstream_without_linked_battery_is_partial(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {"ps": {"values": {"permanentWatts": 0}}},
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        self.assertIn("powerstreams", result["warnings"])
        self.assertEqual(
            result["next_step"],
            "controleer PowerStream koppeling: PowerStream mist gekoppelde accu",
        )

    def test_other_powerstream_data_does_not_satisfy_configured_powerstream(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "other": {
                        "values": {"permanentWatts": 600},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    }
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "actie nodig")
        self.assertIn("powerstreams", result["blocking"])
        checks = {item["key"]: item for item in result["checks"]}
        self.assertEqual(checks["powerstreams"]["details"]["live"], 0)
        self.assertEqual(checks["powerstreams"]["details"]["missing"], 1)
        self.assertEqual(checks["powerstreams"]["details"]["missing_serials"], ["ps"])

    def test_other_powerstream_error_does_not_block_execution(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    },
                    "other": {
                        "strategy_error": "1008 request fail",
                    },
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "klaar")
        checks = {item["key"]: item for item in result["checks"]}
        self.assertEqual(checks["execution"]["details"]["strategy_errors"], 0)

    def test_battery_telemetry_without_soc_is_partial(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"inv.inputWatts": 140}}},
                "powerstreams": {},
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        self.assertIn("batteries", result["warnings"])
        checks = {item["key"]: item for item in result["checks"]}
        self.assertEqual(checks["batteries"]["details"]["live"], 1)
        self.assertEqual(checks["batteries"]["details"]["with_soc"], 0)
        self.assertEqual(checks["batteries"]["details"]["missing_soc"], 1)
        self.assertEqual(
            result["next_step"],
            "controleer EcoFlow batterijdata: batterij-SoC ontbreekt",
        )

    def test_other_battery_telemetry_does_not_satisfy_configured_battery(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"other": {"values": {"pd.soc": 70}}},
                "powerstreams": {},
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "actie nodig")
        self.assertIn("batteries", result["blocking"])
        checks = {item["key"]: item for item in result["checks"]}
        self.assertEqual(checks["batteries"]["details"]["live"], 0)
        self.assertEqual(checks["batteries"]["details"]["missing"], 1)

    def test_battery_soc_limits_do_not_count_as_battery_status(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {
                    "bat": {
                        "values": {
                            "cmsMinDsgSoc": 4,
                            "cmsMaxChgSoc": 98,
                            "backupReverseSoc": 66,
                        }
                    }
                },
                "powerstreams": {},
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        checks = {item["key"]: item for item in result["checks"]}
        self.assertEqual(checks["batteries"]["details"]["with_soc"], 0)
        self.assertEqual(
            checks["batteries"]["message"], "batterij-SoC ontbreekt"
        )

    def test_powerstream_without_linked_soc_is_partial(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                    }
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        self.assertIn("powerstreams", result["warnings"])
        self.assertEqual(
            result["next_step"],
            "controleer PowerStream koppeling: gekoppelde accu-SoC ontbreekt",
        )

    def test_execution_error_blocks_starting_flow(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                    }
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
                "last_powerstream_error": "1008 request fail",
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "actie nodig")
        self.assertIn("execution", result["blocking"])
        self.assertEqual(
            result["next_step"],
            "controleer sturing: laatste PowerStream command faalde",
        )

    def test_throttled_execution_is_partial(self) -> None:
        result = health.dashboard_readiness(
            {
                "price_now": 0.21,
                "prices": [{"price": 0.2}] * 24,
                "price_summary": {"chart": [{"price": 0.2}] * 24},
                "batteries": {"bat": {"values": {"pd.soc": 70}}},
                "powerstreams": {
                    "ps": {
                        "values": {"permanentWatts": 0},
                        "battery_serial": "bat",
                        "battery_soc": 70,
                        "strategy_throttled": True,
                    }
                },
                "corrected_solar_power": 250,
                "weather": {"shortwave_w_m2": 120, "weather_label": "zon"},
                "scenarios": {"a": {}, "b": {}, "c": {}},
            },
            {
                "batteries": [{"serial": "bat"}],
                "powerstreams": [{"serial": "ps"}],
                "homewizard_meters": [{"host": "meter"}],
                "dry_run": False,
            },
        )
        self.assertEqual(result["status"], "gedeeltelijk")
        self.assertIn("execution", result["warnings"])
        self.assertEqual(
            result["next_step"],
            "controleer sturing: wacht op 10-minuten begrenzing",
        )


if __name__ == "__main__":
    unittest.main()
