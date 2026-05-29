"""Integrity checks for shipped Home Assistant artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "custom_components" / "ecoflow_energy_control" / "translations"
USER_VISIBLE_ARTIFACTS = (
    ROOT / "custom_components" / "ecoflow_energy_control" / "manifest.json",
    ROOT / "custom_components" / "ecoflow_energy_control" / "translations" / "en.json",
    ROOT / "custom_components" / "ecoflow_energy_control" / "translations" / "nl.json",
    ROOT / "dashboards" / "ecoflow-energy-control.yaml",
    ROOT / "dashboards" / "ecoflow-energy-powerstreams.yaml",
    ROOT / "dashboards" / "ecoflow-energy-app-style.yaml",
    ROOT / "dashboards" / "ecoflow-energy-scenarios.yaml",
)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    seen: set[str] = set()
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate key: {key}")
        seen.add(key)
        result[key] = value
    return result


class ArtifactIntegrityTest(unittest.TestCase):
    def test_translation_json_has_no_duplicate_keys(self) -> None:
        for path in sorted(TRANSLATIONS.glob("*.json")):
            with self.subTest(path=path.name):
                json.loads(
                    path.read_text(encoding="utf-8"),
                    object_pairs_hook=_reject_duplicate_keys,
                )

    def test_translation_json_does_not_expose_command_json_labels(self) -> None:
        blocked = (
            "EcoFlow command JSON",
            "command JSON",
            "on_command",
            "off_command",
        )
        for path in sorted(TRANSLATIONS.glob("*.json")):
            text = path.read_text(encoding="utf-8")
            for value in blocked:
                with self.subTest(path=path.name, value=value):
                    self.assertNotIn(value, text)

    def test_advanced_options_are_translated(self) -> None:
        for path in sorted(TRANSLATIONS.glob("*.json")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn('"advanced"', text)

    def test_user_visible_artifacts_use_short_app_name(self) -> None:
        blocked = (
            "EcoFlow Energy Control applicatie",
            "Ecoflow Energy Control applicatie",
            "ecoflow energy control applicatie",
        )
        for path in USER_VISIBLE_ARTIFACTS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("EEC app", text)
            for value in blocked:
                with self.subTest(path=path.name, value=value):
                    self.assertNotIn(value, text)


if __name__ == "__main__":
    unittest.main()
