"""Integrity checks for shipped Home Assistant artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "custom_components" / "ecoflow_energy_control" / "translations"
DOMAIN = "ecoflow_energy_control"
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
    def _current_version(self) -> str:
        manifest = json.loads(
            (ROOT / "custom_components" / DOMAIN / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        return str(manifest["version"])

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

    def test_docs_track_current_version_and_presentation_sources(self) -> None:
        version = self._current_version()
        ontwikkeling = (ROOT / "docs" / "ontwikkeling.md").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        pptx = ROOT / "docs" / "eec-app-ontwikkeling.pptx"
        self.assertIn(f"`{version}`", ontwikkeling)
        self.assertIn("docs/eec-app-ontwikkeling.pptx", readme)
        self.assertTrue(pptx.exists())
        self.assertGreater(pptx.stat().st_size, 0)
        for index in range(1, 8):
            with self.subTest(slide=index):
                self.assertTrue(
                    (ROOT / "docs" / "presentation-src" / f"slide-{index:02d}.mjs").exists()
                )

    def test_live_validation_checklist_is_shipped_and_linked(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = (ROOT / "docs" / "live-validatie.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/live-validatie.md", readme)
        for marker in (
            "Flow",
            "Basis",
            "Scenario - nu",
            "Controle",
            "Datacheck",
            "Scenario hulp",
            "Handmatig - tools",
            "EcoFlow bewijs",
            "HomeWizard bewijs",
            "Klaar voor live sturen",
            "Test",
            "Flow > Advies",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, checklist)

    def test_generated_presentation_scratch_is_not_shipped(self) -> None:
        blocked = (
            ROOT / "docs" / "artifact-build-manifest.json",
            ROOT / "outputs",
        )
        for path in blocked:
            with self.subTest(path=path.name):
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
