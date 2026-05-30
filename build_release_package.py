#!/usr/bin/env python3
"""Build a clean GitHub upload package for EEC app."""

from __future__ import annotations

import json
from pathlib import Path
import hashlib
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "ecoflow_energy_control"

RELEASE_ROOT_FILES = (
    ".gitignore",
    "README.md",
    "hacs.json",
)

RELEASE_DIRECTORIES = (
    "custom_components/ecoflow_energy_control",
    "dashboards",
    "docs",
    "tests",
    "tools",
)

SKIP_PARTS = {".git", "__pycache__", "dist", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
SKIP_NAMES = {".DS_Store"}


def _version() -> str:
    manifest = json.loads(
        (ROOT / "custom_components" / DOMAIN / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    return str(manifest["version"])


def _release_files() -> list[str]:
    files: set[str] = set(RELEASE_ROOT_FILES)
    for directory in RELEASE_DIRECTORIES:
        root = ROOT / directory
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(part in SKIP_PARTS for part in relative.parts):
                continue
            if path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES:
                continue
            files.add(relative.as_posix())
    return sorted(files)


def _file_record(relative: str) -> dict[str, object]:
    path = ROOT / relative
    data = path.read_bytes()
    return {
        "path": relative,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _release_manifest(version: str, release_files: list[str]) -> dict[str, object]:
    return {
        "name": "EEC app",
        "version": version,
        "domain": DOMAIN,
        "file_count": len(release_files),
        "files": [_file_record(relative) for relative in release_files],
    }


def main() -> int:
    version = _version()
    output_dir = ROOT / "dist"
    output_dir.mkdir(exist_ok=True)
    package = output_dir / f"eec-app-{version}.zip"
    release_files = _release_files()

    missing = [path for path in release_files if not (ROOT / path).exists()]
    if missing:
        print("EEC release package: ontbrekende bestanden")
        for path in missing:
            print(f"- {path}")
        return 1

    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in release_files:
            path = ROOT / relative
            archive.write(path, relative)
        archive.writestr(
            "release-manifest.json",
            json.dumps(
                _release_manifest(version, release_files),
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )

    print(f"EEC release package: {package}")
    print(f"Bestanden: {len(release_files)}")
    print("Manifest: release-manifest.json")
    print("Upload de inhoud van deze zip naar de root van de GitHub-repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
