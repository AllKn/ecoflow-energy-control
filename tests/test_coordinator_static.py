"""Static checks for executable scenario flow."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "ecoflow_energy_control"
COORDINATOR = COMPONENT / "coordinator.py"
INIT = COMPONENT / "__init__.py"
SERVICES = COMPONENT / "services.yaml"


class CoordinatorStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinator = COORDINATOR.read_text(encoding="utf-8")
        self.init = INIT.read_text(encoding="utf-8")
        self.services = SERVICES.read_text(encoding="utf-8")

    def test_best_scenario_can_be_applied(self) -> None:
        self.assertIn("async_apply_best_scenario", self.coordinator)
        self.assertIn("scenario_is_actionable", self.coordinator)
        self.assertIn(
            '"self_use": (STRATEGY_SELF_USE, POWERSTREAM_STRATEGY_SELF_USE)',
            self.coordinator,
        )
        self.assertIn(
            '"trading": (STRATEGY_EXPORT, POWERSTREAM_STRATEGY_TRADING)',
            self.coordinator,
        )
        self.assertIn(
            '"buffer_50": (STRATEGY_BUFFER_50, POWERSTREAM_STRATEGY_BUFFER_50)',
            self.coordinator,
        )
        self.assertIn("await self.async_apply_strategy()", self.coordinator)

    def test_scenarios_expose_missing_input_warnings(self) -> None:
        self.assertIn("input_warnings = _scenario_input_warnings", self.coordinator)
        self.assertIn("def _scenario_input_warnings", self.coordinator)
        self.assertIn("def _scenario_reason", self.coordinator)
        for marker in (
            "prijs ontbreekt",
            "prijsgrenzen ontbreken",
            "accu-SoC onbekend",
            "input beperkt:",
            '"input_ready": not warnings',
            '"input_warnings": warnings',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.coordinator)

    def test_powerstream_commands_record_manual_or_strategy_source(self) -> None:
        self.assertIn('source: str = "handmatig"', self.coordinator)
        self.assertIn('"command_source"] = source', self.coordinator)
        self.assertIn('"target_watts_source"] = "command"', self.coordinator)
        self.assertIn('"target_watts_source"] = "strategy_command"', self.coordinator)
        self.assertIn('"last_powerstream_source"] = source', self.coordinator)
        self.assertIn('f"dry-run {source} {serial} -> {watts} W"', self.coordinator)
        self.assertIn('f"{source} {serial} -> {watts} W"', self.coordinator)
        self.assertIn('serial, 0, "strategie uit"', self.coordinator)
        self.assertIn('"command_source"] = "strategie"', self.coordinator)
        self.assertIn('"last_powerstream_command": last_strategy_command', self.coordinator)

    def test_powerstream_power_source_is_tracked(self) -> None:
        self.assertIn("_first_number_or_match_with_source", self.coordinator)
        self.assertIn("raw_target_watts, target_watts_source", self.coordinator)
        self.assertIn('"target_watts_source": target_watts_source', self.coordinator)
        self.assertIn('"target_watts_source": "stored_target"', self.coordinator)

    def test_best_scenario_waits_when_not_actionable(self) -> None:
        self.assertIn("if not scenario_is_actionable(scenario):", self.coordinator)
        self.assertIn('"last_action": f"advies wacht:', self.coordinator)

    def test_best_scenario_service_is_registered(self) -> None:
        self.assertIn("SERVICE_APPLY_BEST_SCENARIO", self.init)
        self.assertIn("async_apply_best_scenario", self.init)
        self.assertIn("apply_best_scenario:", self.services)

    def test_all_runtime_services_are_registered_and_documented(self) -> None:
        expected = {
            "SERVICE_SET_POWERSTREAM_WATTS": "set_powerstream_watts",
            "SERVICE_APPLY_STRATEGY": "apply_strategy",
            "SERVICE_APPLY_BEST_SCENARIO": "apply_best_scenario",
            "SERVICE_STOP_POWERSTREAM_EXPORT": "stop_powerstream_export",
            "SERVICE_SET_SMART_PLUG": "set_smart_plug",
        }
        const_text = (COMPONENT / "const.py").read_text(encoding="utf-8")
        for constant, service in expected.items():
            with self.subTest(service=service):
                self.assertIn(f'{constant} = "{service}"', const_text)
                self.assertIn(constant, self.init)
                self.assertIn(f"{service}:", self.services)
                self.assertIn(f"DOMAIN, {constant}", self.init)

    def test_buffer_strategy_has_runtime_policy(self) -> None:
        self.assertIn("STRATEGY_BUFFER_50: POWERSTREAM_STRATEGY_BUFFER_50", self.coordinator)
        policy_text = (COMPONENT / "policy.py").read_text(encoding="utf-8")
        self.assertIn('if strategy == "buffer_50":', policy_text)
        self.assertIn("float(soc) > 50", policy_text)

    def test_global_idle_overrides_stale_group_strategies(self) -> None:
        idle_pos = self.coordinator.index("if self.strategy == STRATEGY_IDLE:")
        group_pos = self.coordinator.index("if self.powerstream_strategies:")
        self.assertLess(idle_pos, group_pos)
        idle_block = self.coordinator[idle_pos:group_pos]
        self.assertIn(
            'await self.async_set_powerstream_watts(serial, 0, "strategie uit")',
            idle_block,
        )
        self.assertIn("await self.async_set_smart_plug(serial, False)", idle_block)
        self.assertIn('"last_action": "strategie uit"', idle_block)

    def test_manual_stop_export_sets_all_powerstreams_to_zero_and_idle(self) -> None:
        self.assertIn("async def async_stop_powerstream_export", self.coordinator)
        block = self.coordinator[
            self.coordinator.index("async def async_stop_powerstream_export") : self.coordinator.index(
                "def _can_update_powerstream_strategy"
            )
        ]
        self.assertIn("POWERSTREAM_STRATEGY_IDLE", block)
        self.assertIn('str(serial), 0, "teruglevering naar 0"', block)
        self.assertIn('"last_action": (', block)

    def test_smart_plug_current_state_is_inferred_from_quotas(self) -> None:
        self.assertIn("def _smart_plug_current_state", self.coordinator)
        self.assertIn('"current_state": current_state', self.coordinator)
        self.assertIn("_smart_plug_current_state(values)", self.coordinator)

    def test_polling_preserves_last_powerstream_command_diagnostics(self) -> None:
        return_block = self.coordinator[
            self.coordinator.index("return {") : self.coordinator.index(
                "async def _async_fetch_weather"
            )
        ]
        self.assertIn('"last_action": previous.get("last_action")', return_block)
        self.assertIn(
            '"last_powerstream_command": previous.get("last_powerstream_command")',
            return_block,
        )
        self.assertIn(
            '"last_powerstream_error": previous.get("last_powerstream_error")',
            return_block,
        )

    def test_polling_refreshes_runtime_settings_from_entry(self) -> None:
        update_block = self.coordinator[
            self.coordinator.index("async def _async_update_data")
            : self.coordinator.index("try:", self.coordinator.index("async def _async_update_data"))
        ]
        self.assertIn("settings = {**self.entry.data, **self.entry.options}", update_block)
        self.assertIn("settings[CONF_DRY_RUN] = self.dry_run", update_block)
        self.assertIn("self.settings = settings", update_block)

    def test_scenario_simulation_totals_are_persisted(self) -> None:
        self.assertIn("from homeassistant.helpers.storage import Store", self.coordinator)
        self.assertIn("SIMULATION_STORE_VERSION", self.coordinator)
        self.assertIn("self._simulation_store", self.coordinator)
        self.assertIn("async def async_load_simulation_state", self.coordinator)
        self.assertIn("async def _async_save_simulation_state", self.coordinator)
        self.assertIn('"scenario_totals": self._scenario_totals', self.coordinator)
        self.assertIn("await self._async_save_simulation_state()", self.coordinator)
        self.assertIn("_coerce_scenario_totals", self.coordinator)
        self.assertIn("await coordinator.async_load_simulation_state()", self.init)

    def test_homewizard_p1_role_is_auto_corrected_from_ha_entities(self) -> None:
        self.assertIn("def _looks_like_homewizard_p1", self.coordinator)
        self.assertIn("energy_import", self.coordinator)
        self.assertIn("energy_export", self.coordinator)
        self.assertIn('"power_l1", "power_l2", "power_l3"', self.coordinator)
        self.assertIn('output.append({**item, "role": role})', self.coordinator)
        self.assertIn("settings[CONF_HOMEWIZARD_METERS] = homewizard_items", self.coordinator)
        self.assertIn("self.settings = settings", self.coordinator)
        self.assertIn("def _looks_like_homewizard_p1", self.init)
        self.assertIn("HOMEWIZARD_ROLE_GRID_METER", self.init)

    def test_direct_delta_solar_feeds_forecast_and_scenarios(self) -> None:
        self.assertIn("CONF_DIRECT_SOLAR_WP", self.coordinator)
        self.assertIn("direct_solar = _direct_solar_summary(settings, weather)", self.coordinator)
        self.assertIn('"direct_solar": direct_solar', self.coordinator)
        self.assertIn("def _direct_solar_summary", self.coordinator)
        self.assertIn("def _direct_solar_forecast_power", self.coordinator)
        self.assertIn("forecast_solar_power = max(", self.coordinator)
        self.assertIn('float(direct_solar.get("forecast_power_w") or 0.0)', self.coordinator)

    def test_corrected_phase_power_can_show_net_consumption(self) -> None:
        self.assertNotIn("phase: max(\n                0.0,", self.coordinator)
        self.assertIn(
            "phase: watts\n            - self._tracked_powerstream_export",
            self.coordinator,
        )

    def test_group_strategy_commands_are_rate_limited_per_powerstream(self) -> None:
        self.assertIn("def _can_update_powerstream_strategy", self.coordinator)
        self.assertIn("def _powerstream_strategy_wait_seconds", self.coordinator)
        self.assertIn("POWERSTREAM_STRATEGY_MIN_INTERVAL_SECONDS", self.coordinator)
        self.assertIn(
            "return max(0, int(POWERSTREAM_STRATEGY_MIN_INTERVAL_SECONDS - elapsed))",
            self.coordinator,
        )

        block = self.coordinator[
            self.coordinator.index("async def _async_apply_group_strategies") : self.coordinator.index(
                "async def _async_send_powerstream_watts"
            )
        ]
        throttle_pos = block.index("if not self._can_update_powerstream_strategy(serial):")
        send_pos = block.index("await self._async_send_powerstream_watts(serial, desired)")
        self.assertLess(throttle_pos, send_pos)
        self.assertIn('"strategy_throttled"] = True', block)
        self.assertIn('"strategy_next_update_seconds"] = self._powerstream_strategy_wait_seconds', block)
        self.assertIn("self._powerstream_last_strategy_set[serial] = dt_util.utcnow()", block)
        self.assertIn('"strategy_throttled"] = False', block)
        self.assertIn(
            '"strategy_next_update_seconds"] = POWERSTREAM_STRATEGY_MIN_INTERVAL_SECONDS',
            block,
        )

    def test_manual_strategy_apply_uses_same_throttled_group_path(self) -> None:
        self.assertIn("async def _async_apply_strategy_groups", self.coordinator)
        apply_block = self.coordinator[
            self.coordinator.index("async def async_apply_strategy") : self.coordinator.index(
                "async def async_apply_best_scenario"
            )
        ]
        self.assertIn("await self._async_apply_strategy_groups", apply_block)
        self.assertIn("POWERSTREAM_STRATEGY_TRADING", apply_block)
        self.assertIn("POWERSTREAM_STRATEGY_BUFFER_50", apply_block)
        self.assertNotIn('await self.async_set_powerstream_watts(serial, target, "strategie")', apply_block)

        helper_block = self.coordinator[
            self.coordinator.index("async def _async_apply_strategy_groups") : self.coordinator.index(
                "async def async_apply_best_scenario"
            )
        ]
        self.assertIn("await self._async_apply_group_strategies", helper_block)
        self.assertIn('"last_powerstream_command": last_strategy_command', helper_block)
        self.assertIn('"strategie wacht op 10-minuten begrenzing"', helper_block)

    def test_smart_plug_forecast_parser_uses_local_datetime_alias(self) -> None:
        start = self.coordinator.index("def _forecast_solar_power_for_horizon")
        end = self.coordinator.index("def _solar_scale_per_m2", start)
        block = self.coordinator[start:end]
        self.assertIn(
            "starts_at = dt_datetime.fromisoformat(str(row.get(\"start\")))", block
        )
        self.assertIsNone(re.search(r"\bdatetime\.fromisoformat\(", block))

    def test_homewizard_reading_prefers_homeassistant_items_by_role(self) -> None:
        coerce_block = self.coordinator[
            self.coordinator.index("def _coerce_homewizard_meters") : self.coordinator.index(
                "def _coerce_homewizard_role", self.coordinator.index("def _coerce_homewizard_meters")
            )
        ]
        self.assertIn("ha_roles", coerce_block)
        self.assertIn("for item in items:", coerce_block)
        self.assertIn('if item.get("source") != "homeassistant":', coerce_block)
        self.assertIn("if role in ha_roles:", coerce_block)
        self.assertIn("return output", coerce_block)


if __name__ == "__main__":
    unittest.main()
