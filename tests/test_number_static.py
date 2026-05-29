"""Static checks for PowerStream number controls."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
NUMBER = ROOT / "custom_components" / "ecoflow_energy_control" / "number.py"


class NumberStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = NUMBER.read_text(encoding="utf-8")

    def test_powerstream_setpoint_exposes_dashboard_context(self) -> None:
        self.assertIn('"eec_sensor_role": "powerstream_setpoint"', self.text)
        for field in (
            "managed_battery_name",
            "managed_battery_soc",
            "managed_battery_free_wh",
            "group_strategy",
            "group_action",
            "decision_reason",
            "suggested_watts",
            "strategy_throttled",
            "strategy_next_update_seconds",
            "strategy_error",
            "command_source",
            "phase",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)

    def test_powerstream_setpoint_uses_watt_limits(self) -> None:
        self.assertIn("self._attr_native_min_value = 0", self.text)
        self.assertIn("self._attr_native_max_value = max(0, max_watts)", self.text)
        self.assertIn("self._attr_native_step = 10", self.text)
        self.assertIn("UnitOfPower.WATT", self.text)


if __name__ == "__main__":
    unittest.main()
