"""Static checks for integration setup upgrade behavior."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components" / "ecoflow_energy_control" / "__init__.py"


class InitStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = INIT.read_text(encoding="utf-8")

    def test_setup_shortens_legacy_entity_registry_names(self) -> None:
        self.assertIn("_shorten_legacy_entity_registry_names(hass, entry)", self.text)
        self.assertIn("from homeassistant.helpers import entity_registry as er", self.text)
        self.assertIn("registry.async_update_entity(entity.entity_id, name=short_name)", self.text)

    def test_legacy_name_cleanup_is_scoped_and_non_destructive(self) -> None:
        start = self.text.index("def _shorten_legacy_entity_registry_names")
        end = self.text.index("def _short_legacy_entity_name")
        block = self.text[start:end]
        self.assertIn("entity.platform != DOMAIN", block)
        self.assertIn("entity.config_entry_id != entry.entry_id", block)
        self.assertIn('getattr(entity, "name", None)', block)
        self.assertNotIn("async_remove", block)

    def test_legacy_name_shortener_only_handles_old_app_prefix(self) -> None:
        start = self.text.index("def _short_legacy_entity_name")
        block = self.text[start:]
        self.assertIn('"EcoFlow Energy Control applicatie"', block)
        self.assertIn('"Ecoflow Energy Control applicatie"', block)
        self.assertIn('"ecoflow energy control applicatie"', block)
        self.assertIn("return APP_NAME", block)
        self.assertIn("return suffix[:1].upper() + suffix[1:]", block)
        self.assertIn("return None", block)
