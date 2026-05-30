"""Packaging checks for HACS/Home Assistant updates."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "ecoflow_energy_control"


class PackagingTest(unittest.TestCase):
    def test_versions_stay_in_sync(self) -> None:
        manifest = json.loads(
            (ROOT / "custom_components" / DOMAIN / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        const_text = (ROOT / "custom_components" / DOMAIN / "const.py").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        const_match = re.search(r'APP_VERSION = "([^"]+)"', const_text)
        readme_match = re.search(r"## Huidige Versie\s+`([^`]+)`", readme)

        self.assertIsNotNone(const_match)
        self.assertIsNotNone(readme_match)
        self.assertEqual(manifest["version"], const_match.group(1))
        self.assertEqual(manifest["version"], readme_match.group(1))

    def test_readme_has_changelog_for_current_version(self) -> None:
        manifest = json.loads(
            (ROOT / "custom_components" / DOMAIN / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"Versie `{manifest['version']}`", readme)

    def test_hacs_points_to_existing_integration_domain(self) -> None:
        hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
        manifest_path = ROOT / "custom_components" / DOMAIN / "manifest.json"
        self.assertTrue(manifest_path.exists())
        self.assertIn(DOMAIN, hacs.get("domains", []))

    def test_required_platform_files_exist(self) -> None:
        component = ROOT / "custom_components" / DOMAIN
        for filename in (
            "__init__.py",
            "manifest.json",
            "config_flow.py",
            "sensor.py",
            "number.py",
            "select.py",
            "switch.py",
            "button.py",
            "health.py",
            "policy.py",
            "power.py",
            ):
            with self.subTest(filename=filename):
                self.assertTrue((component / filename).exists())

    def test_required_api_files_exist(self) -> None:
        api = ROOT / "custom_components" / DOMAIN / "api"
        for filename in (
            "ecoflow.py",
            "homewizard.py",
            "prices.py",
            "sma_cloud.py",
            "weather.py",
        ):
            with self.subTest(filename=filename):
                self.assertTrue((api / filename).exists())

    def test_required_dashboards_exist_and_are_documented(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        filename = "ecoflow-energy-control.yaml"
        self.assertTrue((ROOT / "dashboards" / filename).exists())
        self.assertIn(f"dashboards/{filename}", readme)
        shipped_dashboards = sorted(
            path.name for path in (ROOT / "dashboards").glob("ecoflow-energy-*.yaml")
        )
        self.assertEqual(shipped_dashboards, [filename])


if __name__ == "__main__":
    unittest.main()
