#!/usr/bin/env python3
"""Sync dashboard metadata to manifest version."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "ecoflow_energy_control" / "manifest.json"
DASHBOARD = ROOT / "dashboards" / "ecoflow-energy-control.yaml"


def _read_version() -> str:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return str(manifest["version"])


def _sync_dashboard_text(dashboard: str, version: str) -> str:
    dashboard = re.sub(
        r"^# EEC app dashboard yaml version: .*?$",
        f"# EEC app dashboard yaml version: {version}",
        dashboard,
        count=1,
        flags=re.MULTILINE,
    )
    dashboard = re.sub(
        r"^title:\s*.*$",
        f"title: Ecoflow app [{version}]",
        dashboard,
        count=1,
        flags=re.MULTILINE,
    )
    dashboard = re.sub(
        r"^(\s*- title:)\s*Main\b.*?$",
        f"\\1 Main [{version}]",
        dashboard,
        count=1,
        flags=re.MULTILINE,
    )
    return dashboard


def main() -> int:
    version = _read_version()
    original = DASHBOARD.read_text(encoding="utf-8")
    synced = _sync_dashboard_text(original, version)
    if synced == original:
        print(f"Dashboard versie al synchroon met {version}.")
        return 0

    DASHBOARD.write_text(synced, encoding="utf-8")
    print(f"Dashboard versie bijgewerkt naar {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
