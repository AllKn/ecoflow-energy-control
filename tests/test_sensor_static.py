"""Static checks for sensor discovery attributes used by dashboards."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SENSORS = ROOT / "custom_components" / "ecoflow_energy_control" / "sensor.py"


class SensorStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SENSORS.read_text(encoding="utf-8")

    def test_core_dashboard_sensors_have_discovery_roles(self) -> None:
        for role in (
            "price_now",
            "price_cheap_band",
            "price_expensive_band",
            "corrected_power",
            "grid_flow_state",
            "expected_savings",
            "weather_now",
            "weather_icon_summary",
            "homewizard_raw_power",
            "powerstream_export",
            "app_status",
            "app_version",
            "execution_status",
            "last_action",
            "dashboard_overview",
            "dashboard_setup",
            "dashboard_source_summary",
            "dashboard_ready_state",
            "dashboard_flow_snapshot",
            "dashboard_flow_phase",
            "dashboard_flow_summary",
            "dashboard_value_rate",
            "dashboard_choice_state",
            "dashboard_start_state",
            "dashboard_auto_mode",
            "dashboard_execution_plan",
            "dashboard_command_delta",
            "dashboard_command_needed",
            "dashboard_next_command",
            "dashboard_action_state",
            "decision_context",
            "dashboard_check",
            "scenario_alignment",
            "scenario_choice_summary",
        ):
            with self.subTest(role=role):
                self.assertIn(f'"eec_sensor_role": "{role}"', self.text)

    def test_global_sensors_keep_legacy_dashboard_object_ids(self) -> None:
        self.assertIn("LEGACY_DASHBOARD_OBJECT_PREFIX", self.text)
        self.assertIn("_attr_suggested_object_id", self.text)
        self.assertIn("slugify(", self.text)

    def test_battery_fleet_exposes_storage_and_power_flow(self) -> None:
        self.assertIn("BatteryFleetFreeEnergySensor(coordinator)", self.text)
        self.assertIn("BatteryFleetFreeValueSensor(coordinator)", self.text)
        self.assertIn("BatteryFleetChargePowerSensor(coordinator)", self.text)
        self.assertIn("BatteryFleetDischargePowerSensor(coordinator)", self.text)
        self.assertIn("BatteryFleetNetPowerSensor(coordinator)", self.text)
        self.assertIn('_fleet_attrs("battery_fleet_free_kwh")', self.text)
        self.assertIn('_fleet_attrs("battery_fleet_free_eur")', self.text)
        self.assertIn('_fleet_attrs("battery_fleet_charge_w")', self.text)
        self.assertIn('_fleet_attrs("battery_fleet_discharge_w")', self.text)
        self.assertIn('_fleet_attrs("battery_fleet_net_w")', self.text)
        self.assertIn('"free_kwh"', self.text)
        self.assertIn('"charge_w"', self.text)
        self.assertIn('"discharge_w"', self.text)
        self.assertIn('"net_w"', self.text)

    def test_device_entities_use_short_role_labels_with_friendly_device_names(self) -> None:
        self.assertIn("def _apply_device_entity_label", self.text)
        self.assertIn("_attr_name = label", self.text)
        self.assertIn("LEGACY_DASHBOARD_OBJECT_PREFIX}_{device_name}_{object_suffix}", self.text)
        self.assertIn('super().__init__(coordinator, f"{serial}_soc", "SoC")', self.text)
        self.assertIn('super().__init__(coordinator, f"{serial}_api_status", "API status")', self.text)
        self.assertIn('super().__init__(coordinator, f"{serial}_powerstream_power", "vermogen")', self.text)

    def test_powerstream_groups_expose_free_storage(self) -> None:
        self.assertIn("PowerStreamGroupFreeEnergySensor(coordinator, serial, name)", self.text)
        self.assertIn('f"{serial}_group_free_wh"', self.text)
        self.assertIn('"group_free_wh"', self.text)
        self.assertIn("def _powerstream_group_free_wh", self.text)

    def test_powerstream_groups_expose_advice_delta(self) -> None:
        self.assertIn("PowerStreamGroupSuggestedPowerSensor(coordinator, serial, name)", self.text)
        self.assertIn("PowerStreamGroupDeltaPowerSensor(coordinator, serial, name)", self.text)
        self.assertIn("PowerStreamGroupCommandStatusSensor(coordinator, serial, name)", self.text)
        self.assertIn('f"{serial}_group_suggested_watts"', self.text)
        self.assertIn('f"{serial}_group_delta_watts"', self.text)
        self.assertIn('f"{serial}_group_command_status"', self.text)
        self.assertIn('"group_suggested_watts"', self.text)
        self.assertIn('"group_delta_watts"', self.text)
        self.assertIn('"group_command_status"', self.text)
        self.assertIn("def _powerstream_plan_item", self.text)
        self.assertIn("def _powerstream_plan_attrs", self.text)
        for state in ("ok", "bijsturen", "wacht", "fout"):
            with self.subTest(state=state):
                self.assertIn(f'"{state}"', self.text)

    def test_powerstream_group_action_exposes_charge_conditions(self) -> None:
        for field in (
            "can_charge",
            "can_discharge",
            "charge_blocker",
            "discharge_blocker",
            "managed_battery_free_wh",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)

    def test_scenario_reason_sensor_is_registered(self) -> None:
        self.assertIn("ScenarioReasonSensor(coordinator, scenario_key, label)", self.text)
        self.assertIn('f"scenario_{sensor_role}"', self.text)

    def test_price_and_scenario_sensors_explain_decision_inputs(self) -> None:
        for field in (
            "cheap_band",
            "expensive_band",
            "price_cheap_band",
            "price_expensive_band",
            "corrected_solar_power",
            "basis",
            "input_ready",
            "input_warnings",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)

    def test_weather_forecast_sensors_explain_horizon_context(self) -> None:
        self.assertIn("class WeatherSolarForecastSensor", self.text)
        self.assertIn("WeatherIconSummarySensor(coordinator)", self.text)
        self.assertIn('"eec_sensor_role": "weather_icon_summary"', self.text)
        for field in (
            "horizon_hours",
            "weather_label",
            "weather_icon",
            "icon_summary",
            "temperature",
            "cloud_cover",
            "hourly",
            "unit_note",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)

    def test_scenario_alignment_sensor_is_registered(self) -> None:
        self.assertIn("ScenarioAlignmentSensor(coordinator)", self.text)
        self.assertIn("ScenarioChoiceSummarySensor(coordinator)", self.text)
        self.assertIn("class ScenarioChoiceSummarySensor", self.text)
        self.assertIn('"eec_sensor_role": "scenario_choice_summary"', self.text)
        self.assertIn("def _scenario_choice_summary", self.text)
        self.assertIn("return scenario_choice_summary(", self.text)
        self.assertIn("def _selected_scenario_key", self.text)
        self.assertIn('STRATEGY_EXPORT: "trading"', self.text)
        self.assertIn('STRATEGY_BUFFER_50: "buffer_50"', self.text)
        self.assertIn("selected_data,", self.text)
        self.assertIn("best,", self.text)

    def test_dashboard_check_sensors_are_registered(self) -> None:
        for key in (
            "prices",
            "batteries",
            "powerstreams",
            "solar",
            "weather",
            "scenarios",
            "execution",
        ):
            with self.subTest(key=key):
                self.assertIn(f'DashboardCheckSensor(coordinator, "{key}"', self.text)
        self.assertIn('return f"{status}: {message}"', self.text)
        self.assertIn('def icon(self) -> str:', self.text)
        for icon in (
            "mdi:check-circle",
            "mdi:alert-circle",
            "mdi:close-circle",
            "mdi:help-circle",
        ):
            with self.subTest(icon=icon):
                self.assertIn(icon, self.text)
        self.assertIn('"status": check.get("status", "onbekend")', self.text)
        self.assertIn('"details": check.get("details", {})', self.text)
        self.assertIn('f"detail_{key}": value', self.text)

    def test_dashboard_overview_summarizes_core_counts(self) -> None:
        self.assertIn("class DashboardOverviewSensor", self.text)
        self.assertIn("DashboardSetupSensor(coordinator)", self.text)
        self.assertIn("class DashboardSetupSensor", self.text)
        self.assertIn('"eec_sensor_role": "dashboard_setup"', self.text)
        self.assertIn("def _setup_state", self.text)
        self.assertIn("DashboardSourceSummarySensor(coordinator)", self.text)
        self.assertIn("class DashboardSourceSummarySensor", self.text)
        self.assertIn('"eec_sensor_role": "dashboard_source_summary"', self.text)
        self.assertIn("source_summary(readiness)", self.text)
        for field in (
            "configured_batteries",
            "batteries_with_data",
            "batteries_with_soc",
            "batteries_missing_soc",
            "configured_powerstreams",
            "powerstreams_with_data",
            "price_hours",
            "scenario_count",
            "available_kwh",
            "missing_required",
            "missing_optional",
            "configured_solar_sources",
            "price_source",
            "custom_price_url",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)
        self.assertIn("accu SoC", self.text)
        self.assertIn("minimaal: batterij en prijsbron", self.text)

    def test_overview_and_fleet_only_count_configured_devices(self) -> None:
        self.assertIn("for serial, name in configured.items():", self.text)
        self.assertIn("item = data_batteries.get(serial, {})", self.text)
        self.assertIn("def _configured_live_items", self.text)
        self.assertIn("_configured_batteries_with_soc", self.text)
        self.assertIn("_configured_live_items(powerstreams", self.text)
        self.assertIn("settings = _dashboard_settings(coordinator)", self.text)
        self.assertIn('configured = _configured_items(settings, "powerstreams")', self.text)
        self.assertIn("for device in configured:", self.text)
        self.assertIn("item = powerstreams.get(serial, {})", self.text)

    def test_flow_summary_combines_readiness_strategy_and_power(self) -> None:
        self.assertIn("FlowSnapshotSensor(coordinator)", self.text)
        self.assertIn("FlowPhaseSensor(coordinator)", self.text)
        self.assertIn("class FlowSnapshotSensor", self.text)
        self.assertIn("class FlowPhaseSensor", self.text)
        self.assertIn("FlowReadySensor(coordinator)", self.text)
        self.assertIn("class FlowReadySensor", self.text)
        self.assertIn('"eec_sensor_role": "dashboard_ready_state"', self.text)
        self.assertIn("def _flow_ready_state", self.text)
        self.assertIn("flow_ready_state(", self.text)
        self.assertIn('"eec_sensor_role": "dashboard_flow_snapshot"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_flow_phase"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_value_rate"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_best_power"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_best_day_value"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_best_period_value"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_scenario_input"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_confidence_score"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_confidence_reason"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_choice_delta"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_choice_state"', self.text)
        self.assertIn("FlowValueRateSensor(coordinator)", self.text)
        self.assertIn("FlowBestPowerSensor(coordinator)", self.text)
        self.assertIn("FlowBestDayValueSensor(coordinator)", self.text)
        self.assertIn("FlowBestPeriodValueSensor(coordinator)", self.text)
        self.assertIn("FlowScenarioInputSensor(coordinator)", self.text)
        self.assertIn("FlowConfidenceScoreSensor(coordinator)", self.text)
        self.assertIn("FlowConfidenceReasonSensor(coordinator)", self.text)
        self.assertIn("FlowChoiceDeltaSensor(coordinator)", self.text)
        self.assertIn("FlowChoiceStateSensor(coordinator)", self.text)
        self.assertIn("class FlowValueRateSensor", self.text)
        self.assertIn("class FlowBestPowerSensor", self.text)
        self.assertIn("class FlowBestDayValueSensor", self.text)
        self.assertIn("class FlowBestPeriodValueSensor", self.text)
        self.assertIn("class FlowScenarioInputSensor", self.text)
        self.assertIn("class FlowConfidenceScoreSensor", self.text)
        self.assertIn("class FlowConfidenceReasonSensor", self.text)
        self.assertIn("class FlowChoiceDeltaSensor", self.text)
        self.assertIn("class FlowChoiceStateSensor", self.text)
        self.assertIn('"delta_eur_per_hour"', self.text)
        self.assertIn("positief betekent gemiste waarde", self.text)
        self.assertIn('"best_week_eur"', self.text)
        self.assertIn('"best_month_eur"', self.text)
        self.assertIn("geschat effect van het huidige beste scenario", self.text)
        self.assertIn("def _flow_snapshot", self.text)
        self.assertIn("flow_snapshot_state(readiness, next_action, coordinator.dry_run)", self.text)
        self.assertIn("flow_snapshot_icon(snapshot_state)", self.text)
        self.assertIn("flow_snapshot_phase(snapshot_state)", self.text)
        self.assertIn("snapshot_icon", self.text)
        self.assertIn("FlowSummarySensor(coordinator)", self.text)
        self.assertIn("class FlowSummarySensor", self.text)
        self.assertIn("def _dashboard_settings", self.text)
        for field in (
            "summary",
            "readiness_status",
            "next_step",
            "selected_strategy",
            "best_action",
            "best_reason",
            "best_actionable",
            "start_button_state",
            "start_button_reason",
            "price_context",
            "solar_context",
            "price_now",
            "corrected_solar_power",
            "available_kwh",
            "free_kwh",
            "powerstream_group_count",
            "command_needed_count",
            "next_action",
            "action_state",
            "snapshot_state",
            "snapshot_icon",
            "flow_phase",
            "can_execute",
            "command_required",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)
        self.assertIn(
            "flow_snapshot_state(readiness, next_action, coordinator.dry_run)",
            self.text,
        )
        self.assertIn("flow_snapshot_icon(snapshot_state)", self.text)
        self.assertIn("flow_snapshot_phase(snapshot_state)", self.text)
        self.assertIn("scenario_is_actionable(best)", self.text)
        self.assertIn('next_action = _next_dashboard_action(self.coordinator)', self.text)
        self.assertIn('next_summary = str(next_action.get("summary") or action)', self.text)
        self.assertIn('"next_action_type"', self.text)
        self.assertIn('"advies wacht"', self.text)
        self.assertIn("def _flow_start_state", self.text)
        self.assertIn('"dry_run"] = coordinator.dry_run', self.text)
        for state in ("actie nodig", "wachten", "testmodus", "startbaar"):
            with self.subTest(state=state):
                self.assertIn(f'"{state}"', self.text)

    def test_live_proof_sensor_summarizes_runtime_evidence(self) -> None:
        self.assertIn("DashboardLiveProofSensor(coordinator)", self.text)
        self.assertIn("class DashboardLiveProofSensor", self.text)
        self.assertIn("DashboardProblemSensor(coordinator)", self.text)
        self.assertIn("class DashboardProblemSensor", self.text)
        self.assertIn('"eec_sensor_role": "dashboard_problem"', self.text)
        self.assertIn("def _dashboard_problem", self.text)
        self.assertIn("def _dashboard_check_label", self.text)
        self.assertIn('"severity"', self.text)
        self.assertIn('"blokkeert"', self.text)
        self.assertIn('"let op"', self.text)
        for label in (
            "prijzen",
            "batterijen",
            "PowerStreams",
            "netto opwek",
            "scenario's",
            "sturing",
        ):
            with self.subTest(label=label):
                self.assertIn(label, self.text)
        self.assertIn('"eec_sensor_role": "dashboard_live_proof"', self.text)
        self.assertIn("def _live_proof", self.text)
        for field in (
            "ready_sources",
            "warning_sources",
            "blocking_sources",
            "total_sources",
            "data_ready",
            "data_ready_sources",
            "data_total_sources",
            "execution_status",
            "execution_message",
            "execution_ready",
            "execution_details",
            "proved_keys",
            "warning_keys",
            "blocking_keys",
            "source_statuses",
            "source_messages",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)
        self.assertIn("sturing {proof['execution_status']}", self.text)

    def test_decision_context_explains_why_advice_was_chosen(self) -> None:
        self.assertIn("DecisionContextSensor(coordinator)", self.text)
        self.assertIn("class DecisionContextSensor", self.text)
        self.assertIn('"eec_sensor_role": "decision_context"', self.text)
        self.assertIn("def _price_context_label", self.text)
        self.assertIn("def _solar_context_label", self.text)
        for field in (
            "price_context",
            "solar_context",
            "price_now",
            "corrected_solar_power",
            "available_kwh",
            "free_kwh",
            "best_action",
            "best_actionable",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)

    def test_flow_start_state_is_registered_as_own_sensor(self) -> None:
        self.assertIn("FlowStartStateSensor(coordinator)", self.text)
        self.assertIn("FlowStartReasonSensor(coordinator)", self.text)
        self.assertIn("class FlowStartStateSensor", self.text)
        self.assertIn("class FlowStartReasonSensor", self.text)
        self.assertIn('"eec_sensor_role": "dashboard_start_state"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_start_reason"', self.text)
        self.assertIn("def _start_context", self.text)
        for field in (
            "reason",
            "best_actionable",
            "best_scenario_key",
            "readiness_status",
            "readiness_score",
            "test_mode",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)

    def test_flow_auto_mode_summarizes_automatic_control(self) -> None:
        self.assertIn("FlowAutoModeSensor(coordinator)", self.text)
        self.assertIn("class FlowAutoModeSensor", self.text)
        self.assertIn('"eec_sensor_role": "dashboard_auto_mode"', self.text)
        self.assertIn("def _auto_mode_state", self.text)
        self.assertIn('"mdi:autorenew"', self.text)
        self.assertIn('"mdi:swap-horizontal"', self.text)
        for field in (
            "reason",
            "readiness_status",
            "selected_strategy",
            "best_scenario_key",
            "best_actionable",
            "dry_run",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)
        for state in ("geblokkeerd", "testmodus", "wachten", "uit", "actief", "wijkt af"):
            with self.subTest(state=state):
                self.assertIn(f'"{state}"', self.text)

    def test_flow_execution_plan_summarizes_powerstream_groups(self) -> None:
        self.assertIn("FlowExecutionPlanSensor(coordinator)", self.text)
        self.assertIn("FlowMeasurementStateSensor(coordinator)", self.text)
        self.assertIn("FlowNextCommandSensor(coordinator)", self.text)
        self.assertIn("FlowActionStateSensor(coordinator)", self.text)
        self.assertIn("FlowCommandDeltaSensor(coordinator)", self.text)
        self.assertIn("FlowCommandNeededSensor(coordinator)", self.text)
        self.assertIn("class FlowExecutionPlanSensor", self.text)
        self.assertIn("class FlowMeasurementStateSensor", self.text)
        self.assertIn("class FlowNextCommandSensor", self.text)
        self.assertIn("class FlowActionStateSensor", self.text)
        self.assertIn("class FlowCommandDeltaSensor", self.text)
        self.assertIn("class FlowCommandNeededSensor", self.text)
        self.assertIn('"eec_sensor_role": "dashboard_execution_plan"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_measurement_state"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_next_command"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_action_state"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_command_delta"', self.text)
        self.assertIn('"eec_sensor_role": "dashboard_command_needed"', self.text)
        self.assertIn("def _powerstream_execution_plan", self.text)
        self.assertIn("def _execution_plan_totals", self.text)
        self.assertIn("def _measurement_state", self.text)
        self.assertIn("def _scenario_confidence", self.text)
        self.assertIn("next_dashboard_action(", self.text)
        self.assertIn("def _next_dashboard_action", self.text)
        self.assertIn("dashboard_readiness(coordinator.data or {}", self.text)
        for state in (
            "kan sturen",
            "data nodig",
            "scenario uit",
            "testmodus",
        ):
            with self.subTest(action_state=state):
                self.assertIn(f'"{state}"', self.text)
        for field in (
            "groups",
            "error_count",
            "first_error_name",
            "first_error_message",
            "throttled_count",
            "first_throttled_name",
            "first_throttled_seconds",
            "suggested_total_w",
            "current_total_w",
            "delta_total_w",
            "delta_abs_w",
            "command_needed_count",
            "unknown_current_count",
            "unverified_current_count",
            "managed_battery_name",
            "managed_battery_soc",
            "managed_battery_free_wh",
            "strategy_error",
            "strategy_throttled",
            "command_source",
            "plan_source",
            "delta_watts",
            "command_needed",
            "current_watts_known",
            "current_watts_source",
            "current_watts_verified",
            "verified_current_count",
            "first_unverified_name",
            "first_unverified_source",
            "sources",
            "readiness_score",
            "measurement_state",
            "best_actionable",
            "basis",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)
        self.assertIn('not item.get("current_watts_known")', self.text)
        self.assertIn('item.get("current_watts_verified") is False', self.text)
        self.assertIn("wacht op meting:", self.text)
        self.assertIn('"wacht meting"', self.text)
        self.assertIn('"gemeten"', self.text)
        self.assertIn('"hoog"', self.text)
        self.assertIn('"advies betrouwbaar"', self.text)
        self.assertIn("45% bronnen, 25% input, 20% PowerStream-meting", self.text)
        self.assertIn("powerstream_group_decision", self.text)
        self.assertIn("bijsturen:", self.text)
        self.assertIn("def _power_delta_watts", self.text)
        self.assertIn("_battery_soc_for_serial", self.text)
        self.assertIn("_battery_free_wh_for_serial", self.text)
        self.assertIn("def _powerstream_issue_summary", self.text)

    def test_execution_status_exposes_strategy_errors(self) -> None:
        self.assertIn("class ExecutionStatusSensor", self.text)
        self.assertIn("_powerstream_execution_plan(self.coordinator)", self.text)
        self.assertIn("_powerstream_issue_summary(plan)", self.text)
        self.assertIn('if issues["error_count"]:', self.text)
        self.assertIn('if issues["throttled_count"]:', self.text)
        for field in (
            "last_powerstream_error",
            "error_count",
            "first_error_name",
            "first_error_message",
            "throttled_count",
            "first_throttled_name",
            "strategy_errors",
            "throttled_powerstreams",
            "powerstream_target_count",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)


if __name__ == "__main__":
    unittest.main()
