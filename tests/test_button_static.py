"""Static checks for dashboard action button discovery."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUTTONS = ROOT / "custom_components" / "ecoflow_energy_control" / "button.py"


class ButtonStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = BUTTONS.read_text(encoding="utf-8")

    def test_action_buttons_have_dashboard_roles(self) -> None:
        self.assertEqual(self.text.count('"eec_device_type": "action"'), 5)
        for role in (
            "apply_best_scenario",
            "apply_strategy",
            "stop_powerstream_export",
            "check_ecoflow_api",
            "refresh_prices",
        ):
            with self.subTest(role=role):
                self.assertIn(f'"eec_sensor_role": "{role}"', self.text)

    def test_action_buttons_keep_dashboard_object_ids(self) -> None:
        self.assertIn("LEGACY_DASHBOARD_OBJECT_PREFIX", self.text)
        self.assertIn("_attr_suggested_object_id", self.text)
        for suffix in (
            "_strategie_nu_toepassen",
            "_teruglevering_naar_0",
            "_ecoflow_api_controleren",
            "_epex_prijzen_ophalen",
        ):
            with self.subTest(suffix=suffix):
                self.assertIn(suffix, self.text)

    def test_best_scenario_button_calls_coordinator(self) -> None:
        self.assertIn("ApplyBestScenarioButton(coordinator)", self.text)
        self.assertIn("async_apply_best_scenario", self.text)

    def test_stop_export_button_calls_coordinator(self) -> None:
        self.assertIn("StopPowerstreamExportButton(coordinator)", self.text)
        self.assertIn("async_stop_powerstream_export", self.text)


if __name__ == "__main__":
    unittest.main()
