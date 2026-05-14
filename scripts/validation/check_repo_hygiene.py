"""Run lightweight repository hygiene checks."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BLOCKED_DIR_PARTS = {
    ".git",
    ".terraform",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
}
BLOCKED_FILE_NAMES = {
    ".env",
    "terraform.tfstate",
    "terraform.tfstate.backup",
}
BLOCKED_SUFFIXES = {
    ".pem",
    ".key",
}
BLOCKED_CONTENT = [
    "BEGIN " + "RSA PRIVATE KEY",
    "BEGIN " + "OPENSSH PRIVATE KEY",
    "AK" + "IA",
]


def should_skip(path: Path) -> bool:
    return any(part in BLOCKED_DIR_PARTS for part in path.parts)


def iter_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*") if path.is_file() and not should_skip(path))


def main() -> int:
    errors: list[str] = []

    for path in iter_files():
        rel = path.relative_to(ROOT)
        if path.name in BLOCKED_FILE_NAMES:
            errors.append(f"{rel}: blocked file name")
        if path.suffix in BLOCKED_SUFFIXES:
            errors.append(f"{rel}: blocked secret-like file suffix")

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if "\r\n" in text:
            errors.append(f"{rel}: use LF line endings")

        for marker in BLOCKED_CONTENT:
            if marker in text:
                errors.append(f"{rel}: blocked secret marker {marker!r}")

    if errors:
        print("Repository hygiene check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository hygiene check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
