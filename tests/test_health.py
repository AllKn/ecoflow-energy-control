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
        self.assertEqual(summary["summary"], "prices: geen actuele prijs")
        self.assertEqual(summary["first_issue_key"], "prices")
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
        self.assertEqual(summary["summary"], "weather: geen uurverwachting")
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

    def test_action_needed_when_battery_and_prices_are_missing(self) -> None:
        result = health.dashboard_readiness(
            {"scenarios": {}},
            {"batteries": [{"serial": "bat"}], "powerstreams": [], "dry_run": False},
        )
        self.assertEqual(result["status"], "actie nodig")
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
        self.assertIn("powerstreams", result["warnings"])
        self.assertIn("weather", result["warnings"])
        self.assertEqual(
            result["next_step"],
            "controleer PowerStream koppeling: geen PowerStreams ingesteld",
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
