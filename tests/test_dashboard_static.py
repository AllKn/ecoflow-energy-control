"""Static checks for the primary dashboard."""

from __future__ import annotations

from pathlib import Path
import ast
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_DASHBOARD = ROOT / "dashboards" / "ecoflow-energy-control.yaml"
README = ROOT / "README.md"
FRONTEND_REQUIREMENTS = ROOT / "dashboards" / "frontend-requirements.yaml"


def _declared_frontend_cards() -> set[str]:
    text = FRONTEND_REQUIREMENTS.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*-\s+card:\s+([a-z0-9_-]+)\s*$", text, re.MULTILINE))


class MainDashboardSimpleFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = MAIN_DASHBOARD.read_text(encoding="utf-8")

    def test_contract_has_one_primary_route(self) -> None:
        self.assertIn("# EEC app dashboard yaml version:", self.text)
        self.assertIn("title: Ecoflow app", self.text)
        self.assertIn("  - title: Main", self.text)
        self.assertIn("    path: ecoflow-energy", self.text)
        dashboard_files = sorted(ROOT.glob("dashboards/ecoflow-energy-*.yaml"))
        self.assertEqual(dashboard_files, [MAIN_DASHBOARD])

    def test_top_flow_is_graphical_and_actionable(self) -> None:
        self.assertIn("## Flow", self.text)
        self.assertIn("eec_sensor_role: dashboard_main_summary", self.text)
        self.assertIn("eec_sensor_role: dashboard_insight_state", self.text)
        self.assertIn("eec_sensor_role: dashboard_live_validation", self.text)
        self.assertIn("eec_sensor_role: dashboard_energy_flow", self.text)
        self.assertIn("eec_sensor_role: dashboard_control_verdict", self.text)
        self.assertIn("eec_sensor_role: dashboard_value_rate", self.text)
        self.assertIn("eec_sensor_role: dashboard_next_step", self.text)
        self.assertIn("eec_sensor_role: global_strategy", self.text)
        self.assertIn("eec_sensor_role: test_mode", self.text)
        self.assertIn("eec_sensor_role: apply_best_scenario", self.text)
        start = self.text.index("## Flow")
        end = self.text.index("## Basis")
        block = self.text[start:end]
        self.assertIn("type: button", block)
        self.assertIn("name: Advies starten", block)
        self.assertLessEqual(block.count("eec_sensor_role:"), 12)

    def test_kern_sections_in_expected_order(self) -> None:
        titles = re.findall(r"^\s*## (.+)$", self.text, re.MULTILINE)
        route = [title for title in titles if title in {
            "Flow",
            "Basis",
            "Scenario - uitvoering",
            "Controle & diagnose",
        }]
        self.assertEqual(
            route,
            [
                "Flow",
                "Basis",
                "Scenario - uitvoering",
                "Controle & diagnose",
            ],
        )

    def test_basis_contains_core_live_insights(self) -> None:
        start = self.text.index("## Basis")
        end = self.text.index("## Scenario - uitvoering")
        block = self.text[start:end]
        for role in (
            "corrected_power",
            "grid_flow_state",
            "grid_status",
            "grid_power",
            "price_now",
            "battery_fleet_soc",
            "battery_fleet_available_kwh",
            "battery_fleet_charge_w",
            "battery_fleet_discharge_w",
            "battery_fleet_net_w",
            "powerstream_export",
            "expected_savings",
            "decision_context",
        ):
            self.assertIn(f"eec_sensor_role: {role}", block)

    def test_scenario_card_is_compact(self) -> None:
        start = self.text.index("## Scenario - uitvoering")
        end = self.text.index("## Controle & diagnose")
        block = self.text[start:end]
        for role in (
            "dashboard_scenario_overview",
            "dashboard_scenario_plan",
            "dashboard_action_state",
            "dashboard_confidence_score",
            "dashboard_measurement_state",
            "dashboard_next_command",
        ):
            self.assertIn(f"eec_sensor_role: {role}", block)
        self.assertNotIn("dashboard_best_power", block)
        self.assertNotIn("dashboard_confidence_reason", block)
        self.assertNotIn("dashboard_best_period_value", block)

    def test_smart_plug_is_part_of_dezelfde_flow(self) -> None:
        start = self.text.index("## Scenario - uitvoering")
        end = self.text.index("## Controle & diagnose")
        block = self.text[start:end]
        self.assertIn("eec_sensor_role: smart_plug_control", block)
        self.assertIn("eec_sensor_role: api_status", block)
        self.assertIn("name: Smart Plug", block)
        self.assertIn("name: Smart Plug API", block)
        self.assertIn("type: custom:auto-entities", block)

    def test_controle_is_diagnostische_core(self) -> None:
        start = self.text.index("## Controle & diagnose")
        end = len(self.text)
        block = self.text[start:end]
        for role in (
            "dashboard_overview",
            "dashboard_setup",
            "dashboard_setup_progress",
            "app_status",
            "app_version",
            "dashboard_yaml_version",
            "dashboard_source_summary",
            "dashboard_problem",
            "dashboard_live_proof",
            "dashboard_readiness_score",
            "dashboard_ready_state",
            "dashboard_flow_phase",
            "dashboard_start_state",
            "dashboard_start_reason",
            "dashboard_auto_mode",
            "dashboard_execution_plan",
            "execution_status",
            "last_action",
            "dashboard_check",
            "dashboard_strategy_guide",
            "p1_history",
            "apply_strategy",
            "check_ecoflow_api",
            "refresh_prices",
        ):
            self.assertIn(f"eec_sensor_role: {role}", block)

    def test_secondary_sections_do_not_reappear_as_requirements(self) -> None:
        for title in (
            "Prijsgrenzen",
            "Opslag waarde",
            "Accu's - in/uit",
            "PowerStreams - sturen",
            "PowerStreams - live",
            "Scenario's - details",
            "Uurtarieven - komende 24 uur",
            "Weer",
            "Weer - temperatuur 24 uur",
            "Netto opwek",
            "Diagnose",
        ):
            self.assertNotIn(f"title: {title}", self.text)

    def test_frontend_cards_are_documented(self) -> None:
        readme = README.read_text(encoding="utf-8")
        requirements_text = FRONTEND_REQUIREMENTS.read_text(encoding="utf-8")
        custom_cards = set(re.findall(r"type: custom:([a-z0-9_-]+)", self.text))
        self.assertTrue(custom_cards)
        declared_cards = _declared_frontend_cards()
        self.assertEqual(custom_cards, declared_cards)
        for card in sorted(custom_cards):
            self.assertIn(f"`{card}`", readme)
            self.assertIn(card, requirements_text)

    def test_readme_mentions_single_main_dashboard(self) -> None:
        readme = README.read_text(encoding="utf-8")
        self.assertIn("Het primaire dashboard staat in:", readme)
        self.assertIn("dashboards/ecoflow-energy-control.yaml", readme)
        self.assertIn("Voor normaal gebruik heb je alleen dit dashboard nodig", readme)

    def test_dashboard_sensor_roles_exist_in_runtime_entities(self) -> None:
        runtime_role_files = [
            ROOT
            / "custom_components"
            / "ecoflow_energy_control"
            / "sensor.py",
            ROOT
            / "custom_components"
            / "ecoflow_energy_control"
            / "switch.py",
            ROOT
            / "custom_components"
            / "ecoflow_energy_control"
            / "button.py",
            ROOT
            / "custom_components"
            / "ecoflow_energy_control"
            / "select.py",
            ROOT
            / "custom_components"
            / "ecoflow_energy_control"
            / "number.py",
        ]
        provider_roles = set()
        sensor_text = (ROOT / "custom_components" / "ecoflow_energy_control" / "sensor.py").read_text(
            encoding="utf-8"
        )
        dash_roles = set(re.findall(r"eec_sensor_role:\\s*([a-z0-9_]+)", self.text))

        for path in runtime_role_files:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for key, value in zip(node.keys, node.values):
                        if isinstance(key, ast.Constant) and key.value == "eec_sensor_role":
                            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                                provider_roles.add(value.value)

                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id == "_fleet_attrs" and node.args:
                        arg = node.args[0]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            provider_roles.add(arg.value)
                    if node.func.id == "_device_attrs" and len(node.args) >= 3:
                        arg = node.args[2]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            provider_roles.add(arg.value)
                    if node.func.id == "_scenario_attrs" and len(node.args) >= 3:
                        arg = node.args[2]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            provider_roles.add(f"scenario_{arg.value}")

        for match in re.finditer(
            r"WeatherSolarForecastSensor\\(coordinator,\\s*(\\d+)\\s*\\)",
            sensor_text,
        ):
            provider_roles.add(f"weather_solar_{match.group(1)}h")

        missing = sorted(role for role in sorted(dash_roles) if role not in provider_roles)
        self.assertEqual(
            missing,
            [],
            msg=f"Dashboard roles ontbreken in runtime entity-role contract: {', '.join(missing)}",
        )

    def test_manual_tools_is_escape_hatch(self) -> None:
        text = self.text
        control_pos = text.index("## Controle & diagnose")
        self.assertIn("eec_sensor_role: apply_strategy", text)
        self.assertIn("eec_sensor_role: check_ecoflow_api", text)
        self.assertIn("eec_sensor_role: refresh_prices", text)
        self.assertGreater(text.index("eec_sensor_role: apply_strategy"), control_pos)


if __name__ == "__main__":
    unittest.main()
