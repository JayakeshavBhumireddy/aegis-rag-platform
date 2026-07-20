"""Run local release registry actions with the repository source path configured."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHONPATH_ENTRIES = [
    "packages",
    "services/auth-service/src",
    "services/entitlement-service/src",
    "services/ingestion-service/src",
    "services/observability-service/src",
    "services/policy-service/src",
    "services/context-service/src",
    "services/retrieval-service/src",
    "services/llm-gateway/src",
    "services/verification-service/src",
    "services/assistant-api/src",
    "services/eval-service/src",
]


def main(argv: list[str] | None = None) -> int:
    for entry in reversed(PYTHONPATH_ENTRIES):
        sys.path.insert(0, str(ROOT / entry))
    os.environ.setdefault("UV_CACHE_DIR", str(ROOT / ".uv-cache"))
    from eval_service.release_registry import main as release_main

    return release_main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
