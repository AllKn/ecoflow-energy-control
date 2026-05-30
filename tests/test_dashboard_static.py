"""Static checks for the shipped Lovelace dashboards."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_DASHBOARD = ROOT / "dashboards" / "ecoflow-energy-control.yaml"
OPTIONAL_DASHBOARDS = (
)
README = ROOT / "README.md"
FRONTEND_REQUIREMENTS = ROOT / "dashboards" / "frontend-requirements.yaml"


def _declared_frontend_cards() -> set[str]:
    text = FRONTEND_REQUIREMENTS.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*-\s+card:\s+([a-z0-9_-]+)\s*$", text, re.MULTILINE))


class MainDashboardStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = MAIN_DASHBOARD.read_text(encoding="utf-8")

    def test_new_summary_cards_are_dynamic(self) -> None:
        self.assertIn("eec_device_type: battery_fleet", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_soc", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_available_kwh", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_free_kwh", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_available_eur", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_free_eur", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_charge_w", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_discharge_w", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_net_w", self.text)
        self.assertIn("eec_sensor_role: dashboard_ready_state", self.text)
        self.assertIn("eec_sensor_role: dashboard_main_summary", self.text)
        self.assertIn("eec_sensor_role: dashboard_control_verdict", self.text)
        self.assertIn("eec_sensor_role: dashboard_value_rate", self.text)
        self.assertIn("eec_sensor_role: dashboard_best_power", self.text)
        self.assertIn("eec_sensor_role: dashboard_best_period_value", self.text)
        self.assertIn("eec_sensor_role: dashboard_scenario_overview", self.text)
        self.assertIn("eec_sensor_role: dashboard_scenario_input", self.text)
        self.assertIn("eec_sensor_role: dashboard_confidence_score", self.text)
        self.assertIn("eec_sensor_role: dashboard_confidence_reason", self.text)
        self.assertIn("eec_sensor_role: dashboard_measurement_state", self.text)
        self.assertIn("eec_sensor_role: dashboard_readiness", self.text)
        self.assertIn("eec_sensor_role: dashboard_overview", self.text)
        self.assertIn("eec_sensor_role: dashboard_energy_flow", self.text)
        self.assertIn("eec_sensor_role: dashboard_setup", self.text)
        self.assertIn("eec_sensor_role: dashboard_insight_state", self.text)
        self.assertIn("eec_sensor_role: dashboard_live_proof", self.text)
        self.assertIn("eec_sensor_role: dashboard_live_validation", self.text)
        self.assertIn("eec_sensor_role: dashboard_readiness_score", self.text)
        self.assertIn("eec_sensor_role: dashboard_next_step", self.text)
        self.assertIn("eec_sensor_role: dashboard_check", self.text)
        self.assertIn("eec_device_type: action", self.text)
        self.assertIn("eec_sensor_role: apply_best_scenario", self.text)
        self.assertIn("eec_sensor_role: apply_strategy", self.text)
        self.assertIn("eec_sensor_role: check_ecoflow_api", self.text)
        self.assertIn("eec_sensor_role: refresh_prices", self.text)
        self.assertIn("eec_device_type: control", self.text)
        self.assertIn("eec_sensor_role: global_strategy", self.text)
        self.assertIn("eec_sensor_role: test_mode", self.text)
        self.assertIn("eec_sensor_role: app_status", self.text)
        self.assertIn("eec_sensor_role: execution_status", self.text)
        self.assertIn("eec_sensor_role: last_action", self.text)
        self.assertIn("eec_sensor_role: app_version", self.text)
        self.assertIn("eec_device_type: solar", self.text)
        self.assertIn("eec_sensor_role: corrected_power", self.text)
        self.assertIn("eec_sensor_role: grid_status", self.text)
        self.assertIn("eec_sensor_role: grid_power", self.text)
        self.assertIn("eec_device_type: price", self.text)
        self.assertIn("eec_sensor_role: price_now", self.text)
        self.assertIn("eec_sensor_role: price_cheap_band", self.text)
        self.assertIn("eec_sensor_role: price_expensive_band", self.text)
        self.assertIn("eec_sensor_role: expected_savings", self.text)
        self.assertIn("eec_sensor_role: homewizard_raw_power", self.text)
        self.assertIn("eec_sensor_role: powerstream_export", self.text)
        self.assertIn("eec_sensor_role: powerstream_setpoint", self.text)
        self.assertIn("eec_sensor_role: group_strategy", self.text)
        self.assertIn("eec_sensor_role: group_battery_soc", self.text)
        self.assertIn("eec_sensor_role: group_available_wh", self.text)
        self.assertIn("eec_sensor_role: group_free_wh", self.text)
        self.assertIn("eec_device_type: weather", self.text)
        self.assertIn("eec_sensor_role: weather_now", self.text)
        self.assertIn("eec_sensor_role: weather_icon_summary", self.text)
        self.assertIn("eec_sensor_role: weather_solar_4h", self.text)
        self.assertIn("eec_sensor_role: weather_solar_12h", self.text)
        self.assertIn("eec_sensor_role: weather_solar_24h", self.text)

    def test_main_dashboard_contains_complete_user_flow(self) -> None:
        required_roles = {
            "zien": (
                "dashboard_insight_state",
                "dashboard_main_summary",
                "dashboard_readiness_score",
                "dashboard_ready_state",
                "dashboard_energy_flow",
                "dashboard_value_rate",
                "dashboard_scenario_overview",
                "dashboard_scenario_plan",
                "dashboard_scenario_input",
                "dashboard_confidence_score",
                "dashboard_confidence_reason",
                "dashboard_measurement_state",
                "dashboard_start_state",
                "dashboard_start_reason",
                "dashboard_auto_mode",
                "dashboard_control_verdict",
                "dashboard_next_command",
                "dashboard_action_state",
                "dashboard_check",
                "dashboard_next_step",
                "app_status",
                "execution_status",
                "last_action",
                "dashboard_source_summary",
                "dashboard_live_proof",
            ),
            "kiezen": (
                "global_strategy",
                "test_mode",
                "dashboard_strategy_guide",
                "dashboard_execution_plan",
                "decision_context",
            ),
            "sturen": (
                "apply_best_scenario",
                "apply_strategy",
                "check_ecoflow_api",
                "refresh_prices",
                "powerstream_setpoint",
                "group_strategy",
            ),
            "begrijpen": (
                "price_now",
                "price_cheap_band",
                "price_expensive_band",
                "corrected_power",
                "grid_flow_state",
                "grid_status",
                "grid_power",
                "p1_history",
                "battery_fleet_soc",
                "battery_fleet_available_kwh",
                "battery_fleet_free_kwh",
                "battery_fleet_charge_w",
                "battery_fleet_discharge_w",
                "battery_fleet_net_w",
                "weather_icon_summary",
                "expected_savings",
            ),
        }
        for group, roles in required_roles.items():
            for role in roles:
                with self.subTest(group=group, role=role):
                    self.assertIn(f"eec_sensor_role: {role}", self.text)

    def test_fragile_new_entity_ids_are_not_hardcoded(self) -> None:
        blocked = (
            "sensor.ecoflow_energy_control_applicatie_accu_totaal",
            "sensor.ecoflow_energy_control_applicatie_accu_beschikbaar",
            "sensor.ecoflow_energy_control_applicatie_accu_waarde",
            "sensor.ecoflow_energy_control_applicatie_beste_scenario",
            "button.ecoflow_energy_control_applicatie_strategie_nu_toepassen",
            "button.ecoflow_energy_control_applicatie_ecoflow_api_controleren",
            "button.ecoflow_energy_control_applicatie_epex_prijzen_ophalen",
            "sensor.ecoflow_energy_control_applicatie_opwek_gecorrigeerd",
            "sensor.ecoflow_energy_control_applicatie_stroomprijs_nu",
            "sensor.ecoflow_energy_control_applicatie_verwachte_besparing",
            "sensor.ecoflow_energy_control_applicatie_zon_4_uur",
            "sensor.ecoflow_energy_control_applicatie_zon_12_uur",
            "sensor.ecoflow_energy_control_applicatie_zon_24_uur",
            "state_attr('sensor.ecoflow_energy_control_applicatie_zon_nu'",
            "select.ecoflow_energy_control_applicatie_strategie",
            "switch.ecoflow_energy_control_applicatie_testmodus",
            "sensor.ecoflow_energy_control_applicatie_status",
            "sensor.ecoflow_energy_control_applicatie_versie",
        )
        for entity_id in blocked:
            with self.subTest(entity_id=entity_id):
                self.assertNotIn(entity_id, self.text)

    def test_remaining_hardcoded_entities_are_only_graph_sources(self) -> None:
        found = sorted(
            set(
                re.findall(
                    r"sensor\.ecoflow_energy_control_applicatie_[a-z0-9_]+",
                    self.text,
                )
            )
        )
        self.assertEqual(
            found,
            [
                "sensor.ecoflow_energy_control_applicatie_hoogste_prijs_tot_morgen",
                "sensor.ecoflow_energy_control_applicatie_komende_uren",
                "sensor.ecoflow_energy_control_applicatie_laagste_prijs_tot_morgen",
            ],
        )
        for entity_id in found:
            with self.subTest(entity_id=entity_id):
                self.assertIn(f"entity: {entity_id}", self.text)

    def test_main_flow_sections_exist(self) -> None:
        for title in (
            "title: Flow",
            "title: Basis",
            "title: P1 historie",
            "title: Scenario hulp",
            "title: Controle",
            "title: Waarom",
            "title: Datacheck",
            "title: Handmatig - tools",
            "title: Prijsgrenzen",
            "title: Opslag waarde",
            "title: PowerStreams - sturen",
            "title: PowerStreams - live",
            "title: Scenario's - details",
            "title: Scenario - nu",
            "title: Uurtarieven - komende 24 uur",
            "title: Weer",
            "title: Diagnose",
        ):
            with self.subTest(title=title):
                self.assertIn(title, self.text)

    def test_main_dashboard_daily_route_order_is_explicit(self) -> None:
        titles = re.findall(r"^\s+title: (.+)$", self.text, re.MULTILINE)
        route = [
            title
            for title in titles
            if title
            in {
                "Flow",
                "Basis",
                "Scenario - nu",
                "Controle",
                "Waarom",
                "Datacheck",
                "P1 historie",
                "Scenario hulp",
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
                "Handmatig - tools",
            }
        ]
        self.assertEqual(
            route,
            [
                "Flow",
                "Basis",
                "Scenario - nu",
                "Controle",
                "Waarom",
                "Datacheck",
                "P1 historie",
                "Scenario hulp",
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
                "Handmatig - tools",
            ],
        )

    def test_dashboard_contract_has_one_primary_route(self) -> None:
        self.assertIn("title: EEC app", self.text)
        self.assertIn("  - title: Main", self.text)
        self.assertIn("    path: ecoflow-energy", self.text)
        dashboard_files = sorted(ROOT.glob("dashboards/ecoflow-energy-*.yaml"))
        self.assertEqual(dashboard_files, [MAIN_DASHBOARD])

    def test_readme_points_to_main_dashboard_as_primary_flow(self) -> None:
        readme = README.read_text(encoding="utf-8")
        self.assertIn("Het primaire dashboard staat in:", readme)
        self.assertIn("dashboards/ecoflow-energy-control.yaml", readme)
        self.assertIn("volledige flow", readme)
        self.assertIn("Voor normaal gebruik heb je alleen dit dashboard nodig", readme)
        self.assertIn("Niet-relevante losse dashboards zijn verwijderd", readme)
        for marker in (
            "Voor live validatie na een update kijk je bovenaan naar:",
            "**Flow**",
            "**Basis**",
            "**Scenario - nu**",
            "**Controle > Aandacht**",
            "**Controle > Bewijs**",
            "**Datacheck**",
            "**Flow > Advies** is de normale bediening",
            "**Scenario hulp** is naslag",
            "**Handmatig - tools** is alleen voor diagnose",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, readme)

    def test_top_flow_card_is_executable_and_graphical(self) -> None:
        start = self.text.index("title: Flow")
        end = self.text.index("title: Basis")
        block = self.text[start:end]
        roles = re.findall(r"eec_sensor_role: ([a-z0-9_]+)", block)
        self.assertEqual(
            roles,
            [
                "dashboard_main_summary",
                "dashboard_insight_state",
                "dashboard_live_validation",
                "dashboard_energy_flow",
                "dashboard_control_verdict",
                "dashboard_value_rate",
                "dashboard_next_step",
                "global_strategy",
                "test_mode",
                "apply_best_scenario",
            ],
        )
        self.assertIn("type: grid\n          title: Flow", self.text)
        self.assertIn("columns: 5", block)
        self.assertLessEqual(block.count("eec_sensor_role:"), 10)
        self.assertEqual(block.count("type: tile"), 8)
        self.assertIn("eec_sensor_role: dashboard_main_summary", block)
        self.assertIn("name: Main", block)
        self.assertIn("eec_sensor_role: dashboard_insight_state", block)
        self.assertIn("name: Inzicht", block)
        self.assertNotIn("eec_sensor_role: dashboard_readiness_score", block)
        self.assertNotIn("eec_sensor_role: dashboard_flow_snapshot", block)
        self.assertNotIn("name: Kort", block)
        self.assertIn("eec_sensor_role: dashboard_live_validation", block)
        self.assertIn("name: Live", block)
        self.assertIn("eec_sensor_role: dashboard_energy_flow", block)
        self.assertIn("name: Stroom", block)
        self.assertIn("eec_sensor_role: dashboard_control_verdict", block)
        self.assertIn("name: Nu", block)
        self.assertIn("eec_sensor_role: dashboard_value_rate", block)
        self.assertIn("name: EUR/u", block)
        self.assertIn("min: -1", block)
        self.assertIn("max: 1", block)
        self.assertIn("eec_sensor_role: dashboard_next_step", block)
        self.assertIn("name: Stap", block)
        self.assertNotIn("eec_sensor_role: dashboard_flow_phase", block)
        self.assertNotIn("name: Fase", block)
        self.assertNotIn("eec_sensor_role: dashboard_start_state", block)
        self.assertIn("eec_sensor_role: global_strategy", block)
        self.assertIn("name: Scenario", block)
        self.assertIn("eec_sensor_role: test_mode", block)
        self.assertIn("name: Test", block)
        self.assertNotIn("eec_sensor_role: dashboard_command_delta", block)
        self.assertNotIn("eec_sensor_role: dashboard_command_needed", block)
        self.assertIn("eec_sensor_role: apply_best_scenario", block)
        self.assertIn("type: button", block)
        self.assertIn("icon: mdi:play", block)

    def test_best_scenario_action_is_only_in_primary_flow(self) -> None:
        self.assertEqual(self.text.count("eec_sensor_role: apply_best_scenario"), 1)

    def test_basis_card_shows_core_insights_immediately_after_flow(self) -> None:
        flow_pos = self.text.index("title: Flow")
        basis_pos = self.text.index("title: Basis")
        scenario_pos = self.text.index("title: Scenario - nu")
        control_pos = self.text.index("title: Controle")
        self.assertLess(flow_pos, basis_pos)
        self.assertLess(basis_pos, scenario_pos)
        self.assertLess(scenario_pos, control_pos)
        block = self.text[basis_pos:scenario_pos]
        self.assertIn("type: grid\n          title: Basis", self.text)
        self.assertIn("columns: 6", block)
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
            with self.subTest(role=role):
                self.assertIn(f"eec_sensor_role: {role}", block)
        self.assertIn("name: Context", block)
        self.assertNotIn("eec_sensor_role: p1_history", block)

    def test_p1_history_card_keeps_totals_out_of_live_basis(self) -> None:
        checks_pos = self.text.index("title: Datacheck")
        start = self.text.index("title: P1 historie")
        end = self.text.index("title: Scenario hulp")
        block = self.text[start:end]
        self.assertLess(checks_pos, start)
        self.assertIn("type: grid\n          title: P1 historie", self.text)
        self.assertIn("columns: 3", block)
        self.assertEqual(block.count("eec_sensor_role: p1_history"), 3)
        for period in ("today", "week", "month"):
            with self.subTest(period=period):
                self.assertIn(f"period: {period}", block)
        self.assertIn("name: Dag", block)
        self.assertIn("name: Week", block)
        self.assertIn("name: Maand", block)

    def test_scenario_help_card_avoids_duplicate_controls(self) -> None:
        checks_pos = self.text.index("title: Datacheck")
        start = self.text.index("title: Scenario hulp")
        end = self.text.index("title: Prijsgrenzen")
        block = self.text[start:end]
        self.assertLess(checks_pos, start)
        self.assertIn("type: entities\n          title: Scenario hulp", self.text)
        self.assertIn("eec_device_type: dashboard", block)
        self.assertIn("eec_sensor_role: dashboard_strategy_guide", block)
        self.assertNotIn("eec_sensor_role: global_strategy", block)
        self.assertNotIn("eec_sensor_role: test_mode", block)
        self.assertNotIn("eec_sensor_role: app_status", block)
        self.assertNotIn("eec_sensor_role: execution_status", block)
        self.assertNotIn("eec_sensor_role: last_action", block)
        self.assertNotIn("eec_sensor_role: app_version", block)

    def test_diagnostics_follow_explanation(self) -> None:
        readiness_pos = self.text.index("title: Controle")
        explanation_pos = self.text.index("title: Waarom")
        checks_pos = self.text.index("title: Datacheck")
        history_pos = self.text.index("title: P1 historie")
        help_pos = self.text.index("title: Scenario hulp")
        limits_pos = self.text.index("title: Prijsgrenzen")
        manual_pos = self.text.index("title: Handmatig - tools")
        self.assertLess(readiness_pos, explanation_pos)
        self.assertLess(explanation_pos, checks_pos)
        self.assertLess(checks_pos, history_pos)
        self.assertLess(history_pos, help_pos)
        self.assertLess(help_pos, limits_pos)
        self.assertLess(limits_pos, manual_pos)

    def test_optional_secondary_cards_hide_when_empty(self) -> None:
        for title in (
            "P1 historie",
            "Scenario hulp",
            "Prijsgrenzen",
            "Opslag waarde",
            "Accu's - in/uit",
            "PowerStreams - sturen",
            "PowerStreams - live",
            "Scenario's - details",
            "Weer",
            "Netto opwek",
            "Diagnose",
        ):
            with self.subTest(title=title):
                start = self.text.index(f"title: {title}")
                prefix = self.text[max(0, start - 160):start]
                self.assertIn("type: custom:auto-entities", prefix)
                self.assertIn("show_empty: false", prefix)

    def test_graph_cards_are_conditional_on_source_entities(self) -> None:
        price_start = self.text.index("title: Uurtarieven - komende 24 uur")
        price_block = self.text[max(0, price_start - 420):price_start]
        self.assertIn("type: conditional", price_block)
        self.assertIn(
            "entity: sensor.ecoflow_energy_control_applicatie_laagste_prijs_tot_morgen",
            price_block,
        )
        self.assertIn("state_not: unavailable", price_block)
        self.assertIn("state_not: unknown", price_block)

        weather_start = self.text.index("title: Weer - temperatuur 24 uur")
        weather_block = self.text[max(0, weather_start - 420):weather_start]
        self.assertIn("type: conditional", weather_block)
        self.assertIn(
            "entity: sensor.ecoflow_energy_control_applicatie_komende_uren",
            weather_block,
        )
        self.assertIn("state_not: unavailable", weather_block)
        self.assertIn("state_not: unknown", weather_block)

    def test_advice_card_compares_selected_and_best_scenario(self) -> None:
        start = self.text.index("title: Waarom")
        end = self.text.index("title: Datacheck")
        block = self.text[start:end]
        self.assertNotIn("eec_sensor_role: dashboard_flow_snapshot", block)
        self.assertNotIn("eec_sensor_role: scenario_best", block)
        self.assertNotIn("eec_sensor_role: scenario_alignment", block)
        self.assertNotIn("eec_sensor_role: scenario_choice_summary", block)
        self.assertIn("eec_sensor_role: decision_context", block)
        self.assertIn("eec_sensor_role: dashboard_auto_mode", block)
        self.assertIn("eec_sensor_role: dashboard_start_state", block)
        self.assertIn("eec_sensor_role: dashboard_start_reason", block)
        self.assertIn("eec_sensor_role: dashboard_execution_plan", block)
        self.assertNotIn("eec_sensor_role: dashboard_best_day_value", block)
        self.assertNotIn("eec_sensor_role: dashboard_flow_summary", block)
        self.assertNotIn("eec_sensor_role: dashboard_measurement_state", block)
        self.assertNotIn("eec_sensor_role: dashboard_confidence_reason", block)
        self.assertNotIn("eec_sensor_role: dashboard_next_command", block)
        self.assertIn("eec_sensor_role: execution_status", block)
        self.assertIn("eec_sensor_role: last_action", block)
        self.assertNotIn("eec_sensor_role: dashboard_action_state", block)
        self.assertNotIn("name: Overzicht", block)
        self.assertIn("name: Waarom start", block)
        self.assertNotIn("name: Scenario keuze", block)
        self.assertIn("name: Auto", block)
        self.assertIn("name: Uitvoerplan", block)
        self.assertNotIn("name: Kort advies", block)
        self.assertNotIn("name: Dag EUR", block)
        self.assertNotIn("name: Meting", block)
        self.assertNotIn("name: Zekerheid", block)
        self.assertNotIn("name: Volgende actie", block)
        self.assertIn("name: Sturing", block)
        self.assertIn("name: Laatste actie", block)
        self.assertNotIn("name: Uitvoerbaar", block)

    def test_readiness_card_renders_as_grid_cards(self) -> None:
        start = self.text.index("title: Controle")
        end = self.text.index("title: Waarom")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Controle", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("columns: 6", block)
        self.assertIn("eec_sensor_role: dashboard_overview", block)
        self.assertIn("eec_sensor_role: dashboard_setup", block)
        self.assertIn("eec_sensor_role: dashboard_setup_progress", block)
        self.assertNotIn("eec_sensor_role: dashboard_setup_advice", block)
        sensor_text = (
            ROOT / "custom_components" / "ecoflow_energy_control" / "sensor.py"
        ).read_text(encoding="utf-8")
        self.assertIn('setup.get("current_capability") or setup.get("state")', sensor_text)
        self.assertNotIn("eec_sensor_role: dashboard_insight_state", block)
        self.assertIn("eec_sensor_role: app_status", block)
        self.assertIn("eec_sensor_role: app_version", block)
        self.assertIn("eec_sensor_role: dashboard_source_summary", block)
        self.assertIn("eec_sensor_role: dashboard_problem", block)
        self.assertIn("eec_sensor_role: dashboard_live_proof", block)
        self.assertIn("eec_sensor_role: dashboard_readiness_score", block)
        self.assertIn("eec_sensor_role: dashboard_ready_state", block)
        self.assertIn("eec_sensor_role: dashboard_flow_phase", block)
        self.assertNotIn("eec_sensor_role: dashboard_readiness\n", block)
        self.assertNotIn("eec_sensor_role: dashboard_next_step", block)
        self.assertIn("name: Setup", block)
        self.assertIn("name: Setup %", block)
        self.assertNotIn("name: Setup advies", block)
        self.assertNotIn("name: Advies", block)
        self.assertNotIn("name: Inzicht", block)
        self.assertIn("name: Status", block)
        self.assertIn("name: Versie", block)
        self.assertIn("name: Bronnen", block)
        self.assertIn("name: Aandacht", block)
        self.assertIn("name: Bewijs", block)
        self.assertIn("name: Fase", block)

    def test_data_check_card_is_dynamic(self) -> None:
        start = self.text.index("title: Datacheck")
        end = self.text.index("title: Prijsgrenzen")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Datacheck", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("columns: 4", block)
        self.assertIn("eec_sensor_role: dashboard_check", block)
        self.assertIn("type: tile", block)
        self.assertIn("attribute: check_key", block)

    def test_manual_action_card_is_dynamic_grid(self) -> None:
        start = self.text.index("title: Handmatig - tools")
        end = len(self.text)
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Handmatig - tools", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("columns: 3", block)
        self.assertIn("eec_device_type: action", block)
        self.assertNotIn("eec_sensor_role: apply_best_scenario", block)
        self.assertIn("eec_sensor_role: apply_strategy", block)
        self.assertIn("eec_sensor_role: check_ecoflow_api", block)
        self.assertIn("eec_sensor_role: refresh_prices", block)

    def test_price_limits_card_avoids_basis_duplicates(self) -> None:
        start = self.text.index("title: Prijsgrenzen")
        end = self.text.index("title: Opslag waarde")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Prijsgrenzen", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("columns: 2", block)
        self.assertNotIn("eec_sensor_role: corrected_power", block)
        self.assertNotIn("eec_sensor_role: price_now", block)
        self.assertIn("eec_sensor_role: price_cheap_band", block)
        self.assertIn("eec_sensor_role: price_expensive_band", block)

    def test_storage_value_card_avoids_basis_duplicates(self) -> None:
        start = self.text.index("title: Opslag waarde")
        end = self.text.index("title: Accu's - in/uit")
        block = self.text[start:end]
        self.assertIn("columns: 3", block)
        self.assertNotIn("eec_sensor_role: battery_fleet_soc", block)
        self.assertNotIn("eec_sensor_role: battery_fleet_available_kwh", block)
        self.assertNotIn("eec_sensor_role: expected_savings", block)
        self.assertIn("eec_sensor_role: battery_fleet_free_kwh", block)
        self.assertIn("eec_sensor_role: battery_fleet_available_eur", block)
        self.assertIn("eec_sensor_role: battery_fleet_free_eur", block)
        self.assertIn("eec_sensor_role: battery_fleet_charge_w", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_discharge_w", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_net_w", self.text)

    def test_battery_card_shows_input_output_and_status_per_battery(self) -> None:
        start = self.text.index("title: Accu's - in/uit")
        end = self.text.index("title: PowerStreams - sturen")
        block = self.text[start:end]
        for role in (
            "soc",
            "available_kwh",
            "available_eur",
            "charge_power",
            "charge_source",
            "discharge_power",
            "net_power",
            "mode",
        ):
            with self.subTest(role=role):
                self.assertIn(f"eec_sensor_role: {role}", block)
        self.assertIn("name: In W", block)
        self.assertIn("name: Bron", block)
        self.assertIn("name: Uit W", block)
        self.assertIn("name: Netto W", block)
        self.assertIn("name: Status", block)

    def test_net_solar_card_is_dynamic(self) -> None:
        start = self.text.index("title: Netto opwek")
        end = self.text.index("title: Diagnose")
        block = self.text[start:end]
        self.assertIn("eec_sensor_role: homewizard_raw_power", block)
        self.assertIn("eec_sensor_role: powerstream_export", block)
        self.assertIn("eec_sensor_role: corrected_power", block)
        self.assertIn("eec_sensor_role: grid_power", block)
        self.assertIn("eec_sensor_role: grid_status", block)
        self.assertIn("eec_sensor_role: grid_flow_state", block)

    def test_manual_tools_are_last_diagnostic_escape_hatch(self) -> None:
        diagnostics_pos = self.text.index("title: Diagnose")
        manual_pos = self.text.index("title: Handmatig - tools")
        self.assertLess(diagnostics_pos, manual_pos)

    def test_powerstream_live_card_is_graphical(self) -> None:
        start = self.text.index("title: PowerStreams - live")
        end = self.text.index("title: Scenario's")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: PowerStreams - live", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("eec_sensor_role: power", block)
        self.assertIn("eec_sensor_role: group_suggested_watts", block)
        self.assertIn("eec_sensor_role: group_delta_watts", block)
        self.assertIn("eec_sensor_role: group_command_status", block)
        self.assertIn("eec_sensor_role: group_battery_soc", block)
        self.assertIn("eec_sensor_role: group_available_wh", block)
        self.assertIn("eec_sensor_role: group_free_wh", block)
        self.assertIn("name: Nu W", block)
        self.assertIn("name: Advies W", block)
        self.assertIn("name: Nog W", block)
        self.assertIn("name: Status", block)
        self.assertIn("type: gauge", block)

    def test_powerstream_power_gauge_uses_watts_not_deciwatts(self) -> None:
        start = self.text.index("eec_sensor_role: power")
        end = self.text.index("eec_sensor_role: group_battery_soc")
        block = self.text[start:end]
        self.assertIn("max: 900", block)
        self.assertNotIn("max: 9000", block)

    def test_scenario_details_card_combines_advice_and_effect(self) -> None:
        start = self.text.index("title: Scenario's - details")
        end = self.text.index("title: Uurtarieven - komende 24 uur")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Scenario's - details", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("columns: 2", block)
        self.assertIn("eec_sensor_role: scenario_action", block)
        self.assertIn("eec_sensor_role: scenario_executable", block)
        self.assertIn("eec_sensor_role: scenario_reason", block)
        self.assertIn("eec_sensor_role: scenario_power", block)
        self.assertIn("eec_sensor_role: scenario_eur_per_hour", block)
        self.assertIn("eec_sensor_role: scenario_day_eur", block)
        self.assertIn("type: gauge", block)

    def test_current_scenario_card_summarizes_best_choice_and_execution(self) -> None:
        basis_pos = self.text.index("title: Basis")
        current_pos = self.text.index("title: Scenario - nu")
        control_pos = self.text.index("title: Controle")
        self.assertLess(basis_pos, current_pos)
        self.assertLess(current_pos, control_pos)
        block = self.text[current_pos:control_pos]
        self.assertIn("type: grid\n          title: Scenario - nu", self.text)
        self.assertIn("columns: 5", block)
        for role in (
            "dashboard_action_state",
            "dashboard_scenario_input",
            "dashboard_confidence_score",
            "dashboard_confidence_reason",
            "dashboard_measurement_state",
            "dashboard_value_rate",
            "dashboard_best_power",
            "dashboard_next_command",
            "dashboard_best_period_value",
            "dashboard_scenario_overview",
            "dashboard_scenario_plan",
        ):
            with self.subTest(role=role):
                self.assertIn(f"eec_sensor_role: {role}", block)
        self.assertIn("name: Overzicht", block)
        self.assertIn("name: Plan", block)
        self.assertIn("name: Uitvoerbaar", block)
        sensor_text = (
            ROOT / "custom_components" / "ecoflow_energy_control" / "sensor.py"
        ).read_text(encoding="utf-8")
        self.assertIn("execution_hint", sensor_text)
        self.assertIn("blocked_by", sensor_text)
        self.assertIn("name: Input", block)
        self.assertIn("name: Zeker", block)
        self.assertIn("name: Zekerheid", block)
        self.assertIn("min: 0", block)
        self.assertIn("max: 100", block)
        self.assertIn("name: Meting", block)
        self.assertIn("name: EUR/u", block)
        self.assertIn("name: W", block)
        self.assertIn("name: Volgende", block)
        self.assertIn("name: Totalen", block)

    def test_scenario_advice_includes_reasons(self) -> None:
        start = self.text.index("title: Scenario's - details")
        end = self.text.index("title: Uurtarieven - komende 24 uur")
        block = self.text[start:end]
        self.assertIn("eec_sensor_role: scenario_action", block)
        self.assertIn("eec_sensor_role: scenario_executable", block)
        self.assertIn("eec_sensor_role: scenario_reason", block)

    def test_weather_card_is_dynamic(self) -> None:
        title_start = self.text.index("title: Weer")
        start = self.text.rfind("- type:", 0, title_start)
        end = self.text.index("title: Weer - temperatuur 24 uur")
        block = self.text[start:end]
        self.assertIn("type: custom:auto-entities", block)
        self.assertIn("eec_device_type: weather", block)
        self.assertIn("eec_sensor_role: weather_now", block)
        self.assertIn("eec_sensor_role: weather_icon_summary", block)
        self.assertIn("eec_sensor_role: weather_solar_4h", block)
        self.assertIn("eec_sensor_role: weather_solar_12h", block)
        self.assertIn("eec_sensor_role: weather_solar_24h", block)
        self.assertIn("eec_sensor_role: expected_savings", block)
        self.assertNotIn("state_attr('sensor.ecoflow_energy_control_applicatie_zon_nu'", self.text)


class OptionalDashboardStaticTest(unittest.TestCase):
    def test_custom_dashboard_cards_are_documented(self) -> None:
        readme = README.read_text(encoding="utf-8")
        requirements_text = FRONTEND_REQUIREMENTS.read_text(encoding="utf-8")
        declared_cards = _declared_frontend_cards()
        custom_cards = set()
        text = MAIN_DASHBOARD.read_text(encoding="utf-8")
        custom_cards.update(re.findall(r"type: custom:([a-z0-9_-]+)", text))
        self.assertTrue(custom_cards)
        self.assertEqual(custom_cards, declared_cards)
        for card in sorted(custom_cards):
            with self.subTest(card=card):
                self.assertIn(f"`{card}`", readme)
                self.assertIn(card, requirements_text)

    def test_frontend_requirements_explain_missing_card_effect(self) -> None:
        text = FRONTEND_REQUIREMENTS.read_text(encoding="utf-8")
        cards = _declared_frontend_cards()
        self.assertTrue(cards)
        for card in cards:
            with self.subTest(card=card):
                start = text.index(f"card: {card}")
                next_card = text.find("\n  - card:", start + 1)
                block = text[start: next_card if next_card != -1 else len(text)]
                self.assertIn("hacs_repository:", block)
                self.assertIn("used_for:", block)
                self.assertIn("missing_effect:", block)

    def test_no_separate_feature_dashboards_are_shipped(self) -> None:
        self.assertEqual(OPTIONAL_DASHBOARDS, ())
        dashboard_files = sorted(ROOT.glob("dashboards/ecoflow-energy-*.yaml"))
        self.assertEqual(dashboard_files, [MAIN_DASHBOARD])


if __name__ == "__main__":
    unittest.main()
