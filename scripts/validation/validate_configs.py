"""Validate basic config file syntax.

This script intentionally uses only the Python standard library. It fully
validates JSON syntax and performs lightweight YAML sanity checks until the
project adds a YAML parser dependency.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRS = [
    ROOT / "configs",
    ROOT / "data" / "catalog",
    ROOT / ".github" / "workflows",
]


def validate_json(path: Path) -> list[str]:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
    return []


def validate_yaml_light(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    if "\t" in text:
        errors.append(f"{path}: YAML files must not contain tab indentation")

    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.count("[") != stripped.count("]"):
            errors.append(f"{path}:{line_no}: unmatched square bracket")
        if stripped.count("{") != stripped.count("}"):
            errors.append(f"{path}:{line_no}: unmatched curly brace")

    return errors


def iter_config_files() -> list[Path]:
    files: list[Path] = []
    for directory in CONFIG_DIRS:
        if not directory.exists():
            continue
        files.extend(directory.rglob("*.json"))
        files.extend(directory.rglob("*.yaml"))
        files.extend(directory.rglob("*.yml"))
    return sorted(files)


def main() -> int:
    errors: list[str] = []
    for path in iter_config_files():
        if path.suffix == ".json":
            errors.extend(validate_json(path))
        elif path.suffix in {".yaml", ".yml"}:
            errors.extend(validate_yaml_light(path))

    if errors:
        print("Config validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Config validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

