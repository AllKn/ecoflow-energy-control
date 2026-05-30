"""Tests for power normalization helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "ecoflow_energy_control"
    / "power.py"
)
SPEC = importlib.util.spec_from_file_location("eec_power", MODULE_PATH)
power = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(power)


class PowerNormalizationTest(unittest.TestCase):
    def test_powerstream_deciwatts_are_normalized(self) -> None:
        self.assertEqual(power.normalize_powerstream_watts(5900, 800), 590.0)
        self.assertEqual(power.normalize_powerstream_watts(590, 800), 590.0)

    def test_homewizard_deciwatts_are_normalized(self) -> None:
        self.assertEqual(power.normalize_homewizard_power_w(6000), 600.0)
        self.assertEqual(power.normalize_homewizard_power_w(-6000), -600.0)
        self.assertEqual(power.normalize_homewizard_power_w(600), 600.0)

    def test_homewizard_p1_values_are_not_divided_by_ten(self) -> None:
        self.assertEqual(
            power.normalize_homewizard_power_w(8500, allow_deciwatts=False),
            8500.0,
        )
        self.assertEqual(
            power.normalize_homewizard_power_w(-3200, allow_deciwatts=False),
            -3200.0,
        )

    def test_battery_live_deciwatts_are_normalized(self) -> None:
        self.assertEqual(power.normalize_live_power_w(5900), 590.0)
        self.assertEqual(power.normalize_live_power_w("5900"), 590.0)
        self.assertEqual(power.normalize_live_power_w(590), 590.0)


if __name__ == "__main__":
    unittest.main()
