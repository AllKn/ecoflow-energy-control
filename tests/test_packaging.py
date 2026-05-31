"""Packaging checks for HACS/Home Assistant updates."""

from __future__ import annotations

import json
from pathlib import Path
import re
import hashlib
import subprocess
import sys
import unittest
import zipfile


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
        dashboard = (ROOT / "dashboards" / "ecoflow-energy-control.yaml").read_text(
            encoding="utf-8"
        )

        const_match = re.search(r'APP_VERSION = "([^"]+)"', const_text)
        readme_match = re.search(r"## Huidige Versie\s+`([^`]+)`", readme)
        dashboard_match = re.search(
            r"EEC app dashboard yaml version: ([^\n]+)", dashboard
        )

        self.assertIsNotNone(const_match)
        self.assertIsNotNone(readme_match)
        self.assertIsNotNone(dashboard_match)
        self.assertEqual(manifest["version"], const_match.group(1))
        self.assertEqual(manifest["version"], readme_match.group(1))
        self.assertEqual(manifest["version"], dashboard_match.group(1))

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

    def test_manifest_points_to_public_repository(self) -> None:
        manifest = json.loads(
            (ROOT / "custom_components" / DOMAIN / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            manifest["documentation"],
            "https://github.com/AllKn/ecoflow-energy-control",
        )
        self.assertEqual(
            manifest["issue_tracker"],
            "https://github.com/AllKn/ecoflow-energy-control/issues",
        )

    def test_required_platform_files_exist(self) -> None:
        component = ROOT / "custom_components" / DOMAIN
        for filename in (
            "__init__.py",
            "manifest.json",
            "config_flow.py",
            "dashboard_sync.py",
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

    def test_release_check_passes_for_current_tree(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "release_check.py")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("klaar voor HACS/GitHub", result.stdout)
        self.assertIn("Versie", result.stdout)
        self.assertIn("YAML", result.stdout)

    def test_release_package_tool_lists_required_files(self) -> None:
        tool = (ROOT / "tools" / "build_release_package.py").read_text(
            encoding="utf-8"
        )
        manifest = json.loads(
            (ROOT / "custom_components" / DOMAIN / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_release_package.py")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        package = ROOT / "dist" / f"eec-app-{manifest['version']}.zip"
        self.assertTrue(package.exists())
        with zipfile.ZipFile(package) as archive:
            names = set(archive.namelist())
            release_manifest = json.loads(
                archive.read("release-manifest.json").decode("utf-8")
            )
        for filename in (
            "hacs.json",
            "README.md",
            "custom_components/ecoflow_energy_control/manifest.json",
            "custom_components/ecoflow_energy_control/dashboard.yaml",
            "custom_components/ecoflow_energy_control/dashboard_sync.py",
            "custom_components/ecoflow_energy_control/sensor.py",
            "custom_components/ecoflow_energy_control/translations/nl.json",
            "dashboards/ecoflow-energy-control.yaml",
            "dashboards/frontend-requirements.yaml",
            "docs/live-validatie.md",
            '"tests"',
            "tools/release_check.py",
        ):
            with self.subTest(filename=filename):
                if filename == '"tests"':
                    self.assertIn("tests/test_packaging.py", names)
                else:
                    self.assertIn(filename, names)
        self.assertIn("RELEASE_DIRECTORIES", tool)
        self.assertIn("SKIP_PARTS", tool)
        self.assertIn("_release_manifest", tool)
        self.assertIn("hashlib.sha256", tool)
        self.assertNotIn("dist/eec-app-", "\n".join(names))
        self.assertFalse(any("__pycache__" in name for name in names))
        self.assertFalse(any(name.endswith(".pyc") for name in names))
        self.assertEqual(release_manifest["version"], manifest["version"])
        self.assertEqual(release_manifest["domain"], DOMAIN)
        self.assertEqual(release_manifest["file_count"], len(release_manifest["files"]))
        records = {item["path"]: item for item in release_manifest["files"]}
        for filename in (
            "README.md",
            "custom_components/ecoflow_energy_control/manifest.json",
            "custom_components/ecoflow_energy_control/dashboard.yaml",
            "dashboards/ecoflow-energy-control.yaml",
            "tests/test_packaging.py",
        ):
            with self.subTest(checksum=filename):
                data = (ROOT / filename).read_bytes()
                self.assertEqual(records[filename]["bytes"], len(data))
                self.assertEqual(
                    records[filename]["sha256"],
                    hashlib.sha256(data).hexdigest(),
                )
        self.assertIn("dist", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_component_dashboard_matches_repo_dashboard(self) -> None:
        repo_dashboard = (
            ROOT / "dashboards" / "ecoflow-energy-control.yaml"
        ).read_text(encoding="utf-8")
        component_dashboard = (
            ROOT / "custom_components" / DOMAIN / "dashboard.yaml"
        ).read_text(encoding="utf-8")
        self.assertEqual(component_dashboard, repo_dashboard)


if __name__ == "__main__":
    unittest.main()
