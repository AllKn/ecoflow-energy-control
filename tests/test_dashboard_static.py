"""Static checks for the shipped Lovelace dashboards."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_DASHBOARD = ROOT / "dashboards" / "ecoflow-energy-control.yaml"
OPTIONAL_DASHBOARDS = (
    ROOT / "dashboards" / "ecoflow-energy-powerstreams.yaml",
    ROOT / "dashboards" / "ecoflow-energy-app-style.yaml",
    ROOT / "dashboards" / "ecoflow-energy-scenarios.yaml",
)
README = ROOT / "README.md"


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
        self.assertIn("eec_sensor_role: scenario_best", self.text)
        self.assertIn("eec_sensor_role: scenario_alignment", self.text)
        self.assertIn("eec_sensor_role: dashboard_ready_state", self.text)
        self.assertIn("eec_sensor_role: dashboard_flow_snapshot", self.text)
        self.assertIn("eec_sensor_role: dashboard_flow_summary", self.text)
        self.assertIn("eec_sensor_role: dashboard_value_rate", self.text)
        self.assertIn("eec_sensor_role: dashboard_best_power", self.text)
        self.assertIn("eec_sensor_role: dashboard_best_day_value", self.text)
        self.assertIn("eec_sensor_role: dashboard_best_period_value", self.text)
        self.assertIn("eec_sensor_role: dashboard_scenario_input", self.text)
        self.assertIn("eec_sensor_role: dashboard_confidence_score", self.text)
        self.assertIn("eec_sensor_role: dashboard_confidence_reason", self.text)
        self.assertIn("eec_sensor_role: dashboard_choice_delta", self.text)
        self.assertIn("eec_sensor_role: dashboard_measurement_state", self.text)
        self.assertIn("eec_sensor_role: dashboard_choice_state", self.text)
        self.assertIn("eec_sensor_role: dashboard_readiness", self.text)
        self.assertIn("eec_sensor_role: dashboard_overview", self.text)
        self.assertIn("eec_sensor_role: dashboard_setup", self.text)
        self.assertIn("eec_sensor_role: dashboard_live_proof", self.text)
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
                "dashboard_readiness_score",
                "dashboard_ready_state",
                "dashboard_flow_snapshot",
                "dashboard_flow_summary",
                "dashboard_value_rate",
                "dashboard_scenario_input",
                "dashboard_confidence_score",
                "dashboard_confidence_reason",
                "dashboard_measurement_state",
                "dashboard_choice_state",
                "dashboard_start_state",
                "dashboard_start_reason",
                "dashboard_auto_mode",
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
                "scenario_best",
                "scenario_alignment",
                "scenario_choice_summary",
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
            "title: Keuze wijzigen",
            "title: Gereedheid",
            "title: Datacheck",
            "title: Handmatig",
            "title: Opslag totaal",
            "title: PowerStreams - sturen",
            "title: PowerStreams - live",
            "title: Scenario's - advies",
            "title: Scenario - nu",
            "title: Scenario's - effect",
            "title: Uurtarieven - komende 24 uur",
            "title: Weer",
            "title: Diagnose",
        ):
            with self.subTest(title=title):
                self.assertIn(title, self.text)

    def test_readme_points_to_main_dashboard_as_primary_flow(self) -> None:
        readme = README.read_text(encoding="utf-8")
        self.assertIn("Het primaire dashboard staat in:", readme)
        self.assertIn("dashboards/ecoflow-energy-control.yaml", readme)
        self.assertIn("volledige flow", readme)
        self.assertIn("Optionele detail- en testdashboards", readme)
        for marker in (
            "Voor live validatie na een update kijk je bovenaan naar:",
            "**Flow**",
            "**Basis**",
            "**Scenario - nu**",
            "**Gereedheid > Probleem**",
            "**Gereedheid > Bewijs**",
            "**Datacheck**",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, readme)

    def test_top_flow_card_is_executable_and_graphical(self) -> None:
        start = self.text.index("title: Flow")
        end = self.text.index("title: Basis")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Flow", self.text)
        self.assertIn("columns: 5", block)
        self.assertLessEqual(block.count("eec_sensor_role:"), 10)
        self.assertIn("eec_sensor_role: dashboard_readiness_score", block)
        self.assertIn("eec_sensor_role: dashboard_auto_mode", block)
        self.assertIn("name: Auto", block)
        self.assertIn("eec_sensor_role: dashboard_confidence_score", block)
        self.assertIn("name: Zeker", block)
        self.assertIn("eec_sensor_role: dashboard_best_period_value", block)
        self.assertIn("name: Totalen", block)
        self.assertIn("eec_sensor_role: dashboard_flow_summary", block)
        self.assertIn("eec_sensor_role: dashboard_value_rate", block)
        self.assertIn("name: EUR/u", block)
        self.assertIn("min: -1", block)
        self.assertIn("max: 1", block)
        self.assertIn("eec_sensor_role: dashboard_problem", block)
        self.assertIn("name: Probleem", block)
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
        control_pos = self.text.index("title: Keuze wijzigen")
        self.assertLess(flow_pos, basis_pos)
        self.assertLess(basis_pos, scenario_pos)
        self.assertLess(scenario_pos, control_pos)
        block = self.text[basis_pos:scenario_pos]
        self.assertIn("type: grid\n          title: Basis", self.text)
        self.assertIn("columns: 6", block)
        for role in (
            "corrected_power",
            "grid_flow_state",
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

    def test_control_card_is_dynamic(self) -> None:
        start = self.text.index("title: Keuze wijzigen")
        end = self.text.index("title: Gereedheid")
        block = self.text[start:end]
        self.assertIn("type: entities\n          title: Keuze wijzigen", self.text)
        self.assertIn("eec_device_type: control", block)
        self.assertIn("eec_sensor_role: global_strategy", block)
        self.assertIn("eec_sensor_role: test_mode", block)
        self.assertNotIn("eec_sensor_role: app_status", block)
        self.assertNotIn("eec_sensor_role: execution_status", block)
        self.assertNotIn("eec_sensor_role: last_action", block)
        self.assertNotIn("eec_sensor_role: app_version", block)

    def test_advice_card_compares_selected_and_best_scenario(self) -> None:
        start = self.text.index("title: Advies")
        end = self.text.index("title: Handmatig")
        block = self.text[start:end]
        self.assertIn("eec_sensor_role: dashboard_flow_snapshot", block)
        self.assertIn("eec_sensor_role: scenario_best", block)
        self.assertIn("eec_sensor_role: scenario_alignment", block)
        self.assertIn("eec_sensor_role: scenario_choice_summary", block)
        self.assertIn("eec_sensor_role: decision_context", block)
        self.assertIn("eec_sensor_role: dashboard_start_state", block)
        self.assertIn("eec_sensor_role: dashboard_start_reason", block)
        self.assertIn("eec_sensor_role: dashboard_execution_plan", block)
        self.assertIn("eec_sensor_role: dashboard_best_day_value", block)
        self.assertIn("eec_sensor_role: dashboard_measurement_state", block)
        self.assertIn("eec_sensor_role: dashboard_confidence_reason", block)
        self.assertIn("eec_sensor_role: dashboard_next_command", block)
        self.assertIn("eec_sensor_role: execution_status", block)
        self.assertIn("eec_sensor_role: last_action", block)
        self.assertIn("eec_sensor_role: dashboard_action_state", block)
        self.assertIn("name: Overzicht", block)
        self.assertIn("name: Waarom start", block)
        self.assertIn("name: Scenario keuze", block)
        self.assertIn("name: Uitvoerplan", block)
        self.assertIn("name: Dag EUR", block)
        self.assertIn("name: Meting", block)
        self.assertIn("name: Zekerheid", block)
        self.assertIn("name: Volgende actie", block)
        self.assertIn("name: Sturing", block)
        self.assertIn("name: Laatste actie", block)
        self.assertIn("name: Uitvoerbaar", block)

    def test_readiness_card_renders_as_grid_cards(self) -> None:
        start = self.text.index("title: Gereedheid")
        end = self.text.index("title: Datacheck")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Gereedheid", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("columns: 6", block)
        self.assertIn("eec_sensor_role: dashboard_overview", block)
        self.assertIn("eec_sensor_role: dashboard_setup", block)
        self.assertIn("eec_sensor_role: app_status", block)
        self.assertIn("eec_sensor_role: app_version", block)
        self.assertIn("eec_sensor_role: dashboard_source_summary", block)
        self.assertIn("eec_sensor_role: dashboard_problem", block)
        self.assertIn("eec_sensor_role: dashboard_live_proof", block)
        self.assertIn("name: Setup", block)
        self.assertIn("name: Status", block)
        self.assertIn("name: Versie", block)
        self.assertIn("name: Bronnen", block)
        self.assertIn("name: Probleem", block)
        self.assertIn("name: Bewijs", block)

    def test_data_check_card_is_dynamic(self) -> None:
        start = self.text.index("title: Datacheck")
        end = self.text.index("title: Advies")
        block = self.text[start:end]
        self.assertIn("eec_sensor_role: dashboard_check", block)
        self.assertIn("attribute: check_key", block)

    def test_manual_action_card_is_dynamic_grid(self) -> None:
        start = self.text.index("title: Handmatig")
        end = self.text.index("title: Nu")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Handmatig", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("columns: 3", block)
        self.assertIn("eec_device_type: action", block)
        self.assertNotIn("eec_sensor_role: apply_best_scenario", block)
        self.assertIn("eec_sensor_role: apply_strategy", block)
        self.assertIn("eec_sensor_role: check_ecoflow_api", block)
        self.assertIn("eec_sensor_role: refresh_prices", block)

    def test_now_card_is_dynamic_grid(self) -> None:
        start = self.text.index("title: Nu")
        end = self.text.index("title: Opslag totaal")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Nu", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("columns: 4", block)
        self.assertIn("eec_sensor_role: corrected_power", block)
        self.assertIn("eec_sensor_role: price_now", block)
        self.assertIn("eec_sensor_role: price_cheap_band", block)
        self.assertIn("eec_sensor_role: price_expensive_band", block)

    def test_storage_total_card_shows_available_and_free_capacity(self) -> None:
        start = self.text.index("title: Opslag totaal")
        end = self.text.index("title: Batterijen")
        block = self.text[start:end]
        self.assertIn("columns: 4", block)
        self.assertIn("eec_sensor_role: battery_fleet_available_kwh", block)
        self.assertIn("eec_sensor_role: battery_fleet_free_kwh", block)
        self.assertIn("eec_sensor_role: battery_fleet_available_eur", block)
        self.assertIn("eec_sensor_role: battery_fleet_free_eur", block)
        self.assertIn("eec_sensor_role: battery_fleet_charge_w", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_discharge_w", self.text)
        self.assertIn("eec_sensor_role: battery_fleet_net_w", self.text)

    def test_battery_card_shows_input_output_and_status_per_battery(self) -> None:
        start = self.text.index("title: Batterijen")
        end = self.text.index("title: PowerStreams - sturen")
        block = self.text[start:end]
        for role in (
            "soc",
            "available_kwh",
            "available_eur",
            "charge_power",
            "discharge_power",
            "net_power",
            "mode",
        ):
            with self.subTest(role=role):
                self.assertIn(f"eec_sensor_role: {role}", block)
        self.assertIn("name: In W", block)
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

    def test_scenario_effect_card_is_graphical(self) -> None:
        start = self.text.index("title: Scenario's - effect")
        end = self.text.index("title: Uurtarieven - komende 24 uur")
        block = self.text[start:end]
        self.assertIn("type: grid\n          title: Scenario's - effect", self.text)
        self.assertIn("card_param: cards", block)
        self.assertIn("eec_sensor_role: scenario_power", block)
        self.assertIn("eec_sensor_role: scenario_eur_per_hour", block)
        self.assertIn("eec_sensor_role: scenario_day_eur", block)
        self.assertIn("type: gauge", block)

    def test_current_scenario_card_summarizes_best_choice_and_execution(self) -> None:
        basis_pos = self.text.index("title: Basis")
        current_pos = self.text.index("title: Scenario - nu")
        control_pos = self.text.index("title: Keuze wijzigen")
        self.assertLess(basis_pos, current_pos)
        self.assertLess(current_pos, control_pos)
        block = self.text[current_pos:control_pos]
        self.assertIn("type: grid\n          title: Scenario - nu", self.text)
        self.assertIn("columns: 5", block)
        for role in (
            "scenario_best",
            "scenario_alignment",
            "dashboard_choice_state",
            "dashboard_choice_delta",
            "dashboard_action_state",
            "dashboard_scenario_input",
            "dashboard_confidence_score",
            "dashboard_confidence_reason",
            "dashboard_measurement_state",
            "dashboard_value_rate",
            "dashboard_best_power",
            "dashboard_next_command",
            "dashboard_best_period_value",
        ):
            with self.subTest(role=role):
                self.assertIn(f"eec_sensor_role: {role}", block)
        self.assertIn("name: Beste", block)
        self.assertIn("name: Match", block)
        self.assertIn("name: Keuze", block)
        self.assertIn("name: Mis EUR/u", block)
        self.assertIn("name: Sturen", block)
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
        start = self.text.index("title: Scenario's - advies")
        end = self.text.index("title: Scenario's - effect")
        block = self.text[start:end]
        self.assertIn("eec_sensor_role: scenario_action", block)
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
        dashboards = (MAIN_DASHBOARD, *OPTIONAL_DASHBOARDS)
        custom_cards = set()
        for path in dashboards:
            text = path.read_text(encoding="utf-8")
            custom_cards.update(re.findall(r"type: custom:([a-z0-9_-]+)", text))
        self.assertTrue(custom_cards)
        for card in sorted(custom_cards):
            with self.subTest(card=card):
                self.assertIn(f"`{card}`", readme)

    def test_optional_dashboards_do_not_use_old_fragile_summary_entities(self) -> None:
        blocked = (
            "sensor.ecoflow_energy_control_applicatie_zon_nu",
            "sensor.ecoflow_energy_control_applicatie_zon_4_uur",
            "sensor.ecoflow_energy_control_applicatie_zon_12_uur",
            "sensor.ecoflow_energy_control_applicatie_zon_24_uur",
            "sensor.ecoflow_energy_control_applicatie_verwachte_besparing",
            "sensor.ecoflow_energy_control_applicatie_opwek_gecorrigeerd",
            "sensor.ecoflow_energy_control_applicatie_stroomprijs_nu",
            "sensor.ecoflow_energy_control_applicatie_homewizard_opwek_ruw",
            "sensor.ecoflow_energy_control_applicatie_powerstream_teruglevering",
            "sensor.ecoflow_energy_control_applicatie_status",
            "sensor.ecoflow_energy_control_applicatie_versie",
            "state_attr('sensor.ecoflow_energy_control_applicatie_zon_nu'",
        )
        for path in OPTIONAL_DASHBOARDS:
            text = path.read_text(encoding="utf-8")
            for entity_id in blocked:
                with self.subTest(path=path.name, entity_id=entity_id):
                    self.assertNotIn(entity_id, text)

    def test_optional_dashboards_use_discovery_for_core_cards(self) -> None:
        required = {
            "ecoflow-energy-powerstreams.yaml": (
                "eec_sensor_role: test_mode",
                "eec_sensor_role: global_strategy",
                "eec_sensor_role: price_now",
                "eec_sensor_role: corrected_power",
                "eec_sensor_role: weather_icon_summary",
                "eec_sensor_role: weather_solar_24h",
                "eec_sensor_role: powerstream_setpoint",
            ),
            "ecoflow-energy-app-style.yaml": (
                "eec_sensor_role: price_now",
                "eec_sensor_role: corrected_power",
                "eec_sensor_role: homewizard_raw_power",
                "eec_sensor_role: powerstream_export",
                "eec_sensor_role: weather_icon_summary",
                "eec_sensor_role: powerstream_setpoint",
            ),
            "ecoflow-energy-scenarios.yaml": (
                "eec_sensor_role: app_version",
                "eec_sensor_role: price_now",
                "eec_sensor_role: corrected_power",
                "eec_sensor_role: app_status",
                "eec_sensor_role: scenario_eur_per_hour",
            ),
        }
        for path in OPTIONAL_DASHBOARDS:
            text = path.read_text(encoding="utf-8")
            for needle in required[path.name]:
                with self.subTest(path=path.name, needle=needle):
                    self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
