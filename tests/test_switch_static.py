"""Static checks for dashboard switch discovery."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SWITCH = ROOT / "custom_components" / "ecoflow_energy_control" / "switch.py"


class SwitchStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SWITCH.read_text(encoding="utf-8")

    def test_test_mode_switch_has_dashboard_role(self) -> None:
        self.assertIn('"eec_device_type": "control"', self.text)
        self.assertIn('"eec_sensor_role": "test_mode"', self.text)
        self.assertIn("LEGACY_DASHBOARD_OBJECT_PREFIX", self.text)
        self.assertIn("_attr_suggested_object_id", self.text)
        self.assertIn("_testmodus", self.text)

    def test_test_mode_switch_updates_runtime_settings_for_dashboard(self) -> None:
        self.assertIn("CONF_DRY_RUN", self.text)
        self.assertIn("self.coordinator.settings[CONF_DRY_RUN] = True", self.text)
        self.assertIn("self.coordinator.settings[CONF_DRY_RUN] = False", self.text)

    def test_smart_plug_switch_entities_are_discovered_on_dashboard(self) -> None:
        self.assertIn("SmartPlugSwitch(coordinator, str(serial), str(device.get(\"name\", serial)))", self.text)
        self.assertIn('"eec_device_type": "smart_plug"', self.text)
        self.assertIn('"eec_sensor_role": "smart_plug_control"', self.text)
        self.assertIn('"schedule_enabled"', self.text)
        self.assertIn('"last_command"', self.text)
        self.assertIn('"current_state"', self.text)
        self.assertIn('item.get("current_state")', self.text)


if __name__ == "__main__":
    unittest.main()
