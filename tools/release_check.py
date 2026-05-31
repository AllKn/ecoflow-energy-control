#!/usr/bin/env python3
"""Check whether the local EEC app tree is ready for a HACS update."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "ecoflow_energy_control"
REPO_URL = "https://github.com/AllKn/ecoflow-energy-control"
DASHBOARD = "ecoflow-energy-control.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _match(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text)
    if not match:
        raise AssertionError(f"mist {label}")
    return match.group(1)


def main() -> int:
    manifest_path = ROOT / "custom_components" / DOMAIN / "manifest.json"
    const_path = ROOT / "custom_components" / DOMAIN / "const.py"
    dashboard_path = ROOT / "dashboards" / DASHBOARD
    readme_path = ROOT / "README.md"

    manifest = json.loads(_read(manifest_path))
    const_text = _read(const_path)
    dashboard_text = _read(dashboard_path)
    readme = _read(readme_path)
    hacs = json.loads(_read(ROOT / "hacs.json"))

    version = str(manifest["version"])
    checks = [
        ("APP_VERSION", version == _match(r'APP_VERSION = "([^"]+)"', const_text, "APP_VERSION")),
        ("README versie", version == _match(r"## Huidige Versie\s+`([^`]+)`", readme, "README versie")),
        (
            "dashboard YAML versie",
            version
            == _match(
                r"EEC app dashboard yaml version: ([^\n]+)",
                dashboard_text,
                "dashboard YAML versie",
            ),
        ),
        (
            "dashboard titel versie",
            version
            == _match(
                r"title:\s*Ecoflow app \[([^\]]+)\]",
                dashboard_text,
                "dashboard titel versie",
            ),
        ),
        (
            "dashboard hoofdpagina versie",
            version
            == _match(
                r"\s*-\s*title:\s*Main \[([^\]]+)\]",
                dashboard_text,
                "dashboard hoofdpagina versie",
            ),
        ),
        ("README changelog", f"Versie `{version}`" in readme),
        ("HACS domein", DOMAIN in hacs.get("domains", [])),
        ("documentatie link", manifest.get("documentation") == REPO_URL),
        ("issue link", manifest.get("issue_tracker") == f"{REPO_URL}/issues"),
        (
            "een hoofd-dashboard",
            sorted(path.name for path in (ROOT / "dashboards").glob("ecoflow-energy-*.yaml"))
            == [DASHBOARD],
        ),
    ]

    failed = [label for label, ok in checks if not ok]
    if failed:
        print("EEC release check: NIET KLAAR")
        for label in failed:
            print(f"- {label}")
        return 1

    print(f"EEC release check: klaar voor HACS/GitHub ({version})")
    print("")
    print("python3 tools/sync_dashboard_version.py")
    print(f'git add . && git commit -m "release: {version}" && git push')
    print("")
    print("Na publiceren op GitHub:")
    print("1. Laat HACS de repository opnieuw downloaden.")
    print("2. Herstart Home Assistant.")
    print("3. Importeer of vervang het hoofd-dashboard opnieuw als de YAML-tegel ontbreekt.")
    print(f"4. Controleer op het dashboard: Versie {version} en YAML {version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
