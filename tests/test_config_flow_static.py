"""Static checks for the simple first-run configuration flow."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FLOW = ROOT / "custom_components" / "ecoflow_energy_control" / "config_flow.py"
README = ROOT / "README.md"


class ConfigFlowStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = CONFIG_FLOW.read_text(encoding="utf-8")
        self.user_step = self.text[
            self.text.index("async def async_step_user") : self.text.index(
                "async def _validate_ecoflow_credentials"
            )
        ]

    def test_first_setup_only_requires_identity_and_ecoflow_keys(self) -> None:
        self.assertIn("vol.Required(\n                    CONF_NAME", self.user_step)
        self.assertIn("vol.Required(CONF_ACCESS_KEY)", self.user_step)
        self.assertIn("vol.Required(CONF_SECRET_KEY)", self.user_step)

        for hidden_field in (
            "CONF_PRICE_SOURCE",
            "CONF_PRICE_PROVIDER",
            "CONF_PRICE_INTERVAL",
            "CONF_PRICE_SURCHARGE",
            "CONF_SMA_API_HOST",
            "CONF_SMA_TOKEN",
            "CONF_DRY_RUN",
        ):
            with self.subTest(hidden_field=hidden_field):
                self.assertNotIn(f"vol.Required({hidden_field}", self.user_step)
                self.assertNotIn(f"vol.Optional({hidden_field}", self.user_step)

    def test_initial_defaults_cover_hidden_basic_settings(self) -> None:
        defaults = self.text[
            self.text.index("def _initial_setup_defaults") : self.text.index(
                "class EcoFlowEnergyConfigFlow"
            )
        ]
        for field in (
            "CONF_ECOFLOW_HOST",
            "CONF_PRICE_SOURCE",
            "CONF_PRICE_PROVIDER",
            "CONF_PRICE_INTERVAL",
            "CONF_PRICE_SURCHARGE",
            "CONF_PRICE_INCL_VAT",
            "CONF_WEATHER_CITY",
            "CONF_DRY_RUN",
            "CONF_BATTERIES",
            "CONF_POWERSTREAMS",
            "CONF_HOMEWIZARD_METERS",
        ):
            with self.subTest(field=field):
                self.assertIn(field, defaults)

    def test_import_flows_are_listed_before_manual_add(self) -> None:
        menu = self.text[
            self.text.index("menu_options=[") : self.text.index(
                "async def async_step_import_homewizard"
            )
        ]
        self.assertLess(menu.index('"import_ecoflow"'), menu.index('"add_device"'))
        self.assertLess(menu.index('"import_homewizard"'), menu.index('"add_device"'))
        self.assertLess(menu.index('"add_device"'), menu.index('"general"'))
        self.assertLess(menu.index('"remove_device"'), menu.index('"advanced"'))

    def test_readme_documents_device_first_configuration_order(self) -> None:
        readme = README.read_text(encoding="utf-8")
        devices_pos = readme.index("**EcoFlow apparaten importeren**")
        homewizard_pos = readme.index("**HomeWizard importeren**")
        add_pos = readme.index("**Handmatig toevoegen**")
        general_pos = readme.index("**Basisinstellingen**")
        advanced_pos = readme.index("**Technische instellingen**")
        self.assertLess(devices_pos, add_pos)
        self.assertLess(homewizard_pos, add_pos)
        self.assertLess(add_pos, general_pos)
        self.assertLess(general_pos, advanced_pos)
        self.assertIn("De app controleert de verbinding", readme)

    def test_ecoflow_import_suggests_device_type_from_api_metadata(self) -> None:
        configure = self.text[
            self.text.index("async def async_step_import_ecoflow_configure") : self.text.index(
                "async def async_step_import_ecoflow_powerstream"
            )
        ]
        self.assertIn("suggested_type = _suggest_ecoflow_device_type", configure)
        self.assertIn('vol.Required("device_type", default=suggested_type)', configure)
        self.assertIn('"suggested_type": _ecoflow_device_type_label', configure)
        helper = self.text[self.text.index("def _suggest_ecoflow_device_type") :]
        for marker in ("powerstream", "smart_plug", "delta_pro_3", "delta_pro"):
            with self.subTest(marker=marker):
                self.assertIn(f'return "{marker}"', helper)

    def test_general_settings_keep_only_common_controls(self) -> None:
        general = self.text[
            self.text.index("async def async_step_general") : self.text.index(
                "async def async_step_advanced"
            )
        ]
        for field in (
            "CONF_PRICE_SOURCE",
            "CONF_PRICE_SURCHARGE",
            "CONF_WEATHER_CITY",
            "CONF_DRY_RUN",
        ):
            with self.subTest(field=field):
                self.assertIn(field, general)
        for technical_field in (
            "CONF_ECOFLOW_HOST",
            "CONF_ACCESS_KEY",
            "CONF_SECRET_KEY",
            "CONF_PRICE_URL",
            "CONF_SMA_API_HOST",
            "CONF_SMA_TOKEN",
            "CONF_SMA_ENDPOINT",
        ):
            with self.subTest(technical_field=technical_field):
                self.assertNotIn(technical_field, general)

    def test_translations_keep_options_menu_plain_language(self) -> None:
        translations = {
            "nl": (
                ROOT
                / "custom_components"
                / "ecoflow_energy_control"
                / "translations"
                / "nl.json"
            ).read_text(encoding="utf-8"),
            "en": (
                ROOT
                / "custom_components"
                / "ecoflow_energy_control"
                / "translations"
                / "en.json"
            ).read_text(encoding="utf-8"),
        }
        expected = {
            "nl": (
                "Basisinstellingen",
                "Technische instellingen",
                "verbinding wordt gecontroleerd",
                "Handmatig toevoegen",
            ),
            "en": (
                "Basic settings",
                "Technical settings",
                "connection is checked",
                "Add manually",
            ),
        }
        for language, text in translations.items():
            for marker in expected[language]:
                with self.subTest(language=language, marker=marker):
                    self.assertIn(marker, text)

    def test_manual_add_does_not_duplicate_import_routes(self) -> None:
        add_device = self.text[
            self.text.index("async def async_step_add_device") : self.text.index(
                "async def async_step_general"
            )
        ]
        self.assertIn('"homewizard": "HomeWizard lokale meter"', add_device)
        self.assertIn('"sma": "SMA cloud omvormer"', add_device)
        self.assertNotIn("homewizard_ha", add_device)
        self.assertIn('"import_homewizard"', self.text)

    def test_advanced_settings_hold_technical_controls(self) -> None:
        advanced = self.text[
            self.text.index("async def async_step_advanced") : self.text.index(
                "async def async_step_add_battery"
            )
        ]
        for field in (
            "CONF_ECOFLOW_HOST",
            "CONF_ACCESS_KEY",
            "CONF_SECRET_KEY",
            "CONF_PRICE_PROVIDER",
            "CONF_PRICE_INTERVAL",
            "CONF_PRICE_INCL_VAT",
            "CONF_PRICE_URL",
            "CONF_SMA_API_HOST",
            "CONF_SMA_TOKEN",
            "CONF_SMA_PLANT_ID",
            "CONF_SMA_ENDPOINT",
        ):
            with self.subTest(field=field):
                self.assertIn(field, advanced)

    def test_save_merges_with_existing_settings_and_clears_options(self) -> None:
        save = self.text[
            self.text.index("def _save") : self.text.index("def _edit_context")
        ]
        self.assertIn("merged = self._settings()", save)
        self.assertIn("merged.update(values)", save)
        self.assertIn("data=merged", save)
        self.assertIn("options={}", save)
        self.assertIn("async_reload(self._entry.entry_id)", save)

    def test_general_and_advanced_settings_use_merge_save(self) -> None:
        general = self.text[
            self.text.index("async def async_step_general") : self.text.index(
                "async def async_step_advanced"
            )
        ]
        advanced = self.text[
            self.text.index("async def async_step_advanced") : self.text.index(
                "async def async_step_add_battery"
            )
        ]
        self.assertIn("return self._save(user_input)", general)
        self.assertIn("return self._save(user_input)", advanced)

    def test_manual_powerstream_form_hides_command_json(self) -> None:
        step = self.text[
            self.text.index("async def async_step_device_powerstream") : self.text.index(
                "async def async_step_add_sma"
            )
        ]
        form = step[step.index('step_id="device_powerstream"') :]
        self.assertNotIn('vol.Required(\n                        "command"', form)
        self.assertIn('"command": DEFAULT_POWERSTREAM_COMMAND', step)
        self.assertIn('default=self._default_battery_serial()', step)

    def test_powerstream_import_preselects_only_battery_when_safe(self) -> None:
        step = self.text[
            self.text.index("async def async_step_import_ecoflow_powerstream") : self.text.index(
                "async def async_step_import_ecoflow_smart_plug"
            )
        ]
        self.assertIn('default=self._default_battery_serial()', step)
        helper = self.text[
            self.text.index("def _default_battery_serial") : self.text.index(
                "def _homewizard_ha_configured"
            )
        ]
        self.assertIn("if len(choices) == 1:", helper)
        self.assertIn("return next(iter(choices))", helper)
        self.assertIn('return ""', helper)

    def test_manual_smart_plug_form_hides_command_json(self) -> None:
        step = self.text[
            self.text.index("async def async_step_device_smart_plug") : self.text.index(
                "async def async_step_remove_device"
            )
        ]
        form = step[step.index('step_id="device_smart_plug"') :]
        self.assertNotIn('vol.Required(\n                        "on_command"', form)
        self.assertNotIn('vol.Required(\n                        "off_command"', form)
        self.assertIn('"on_command": DEFAULT_SMART_PLUG_ON_COMMAND', step)
        self.assertIn('"off_command": DEFAULT_SMART_PLUG_OFF_COMMAND', step)


if __name__ == "__main__":
    unittest.main()
