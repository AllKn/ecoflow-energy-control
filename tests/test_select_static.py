"""Static checks for human-readable strategy selects."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SELECT = ROOT / "custom_components" / "ecoflow_energy_control" / "select.py"


class SelectStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SELECT.read_text(encoding="utf-8")

    def test_strategy_selects_use_human_labels(self) -> None:
        for label in ("Eigen gebruik", "Terugleveren", "Handelen", "Buffer 50%", "Uit"):
            with self.subTest(label=label):
                self.assertIn(label, self.text)

    def test_strategy_selects_still_accept_internal_values(self) -> None:
        self.assertIn("STRATEGY_VALUES.get(option, option)", self.text)
        self.assertIn("POWERSTREAM_STRATEGY_VALUES.get(option, option)", self.text)

    def test_global_strategy_has_dashboard_role(self) -> None:
        self.assertIn('"eec_device_type": "control"', self.text)
        self.assertIn('"eec_sensor_role": "global_strategy"', self.text)
        self.assertIn("LEGACY_DASHBOARD_OBJECT_PREFIX", self.text)
        self.assertIn("_attr_suggested_object_id", self.text)
        self.assertIn("_strategie", self.text)

    def test_powerstream_strategy_exposes_dashboard_context(self) -> None:
        self.assertIn('"eec_sensor_role": "group_strategy"', self.text)
        for field in (
            "managed_battery_name",
            "managed_battery_soc",
            "managed_battery_free_wh",
            "suggested_watts",
            "action",
            "decision_reason",
            "strategy_throttled",
            "strategy_next_update_seconds",
            "strategy_error",
        ):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', self.text)


if __name__ == "__main__":
    unittest.main()
