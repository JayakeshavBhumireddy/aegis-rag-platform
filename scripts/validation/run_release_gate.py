"""Run the local release gate for the AegisRAG functional slice."""

from __future__ import annotations

import os
import subprocess
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
    "services/reranker-service/src",
    "services/llm-gateway/src",
    "services/verification-service/src",
    "services/assistant-api/src",
    "services/eval-service/src",
]


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(ROOT / entry) for entry in PYTHONPATH_ENTRIES)
    env.setdefault("UV_CACHE_DIR", str(ROOT / ".uv-cache"))

    commands = [
        [sys.executable, "scripts/data/generate_synthetic_corpus.py"],
        ["uv", "run", "python", "-m", "ingestion_service.pipeline"],
        [sys.executable, "scripts/validation/validate_configs.py"],
        [sys.executable, "scripts/validation/check_repo_hygiene.py"],
        [sys.executable, "scripts/validation/validate_runtime_packaging.py"],
        [sys.executable, "scripts/validation/validate_infra_contracts.py"],
        ["uv", "run", "python", "scripts/validation/validate_api_contracts.py"],
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "pytest", "-q"],
        ["uv", "run", "python", "-m", "eval_service.runner"],
        ["uv", "run", "python", "-m", "eval_service.release_registry"],
    ]

    for command in commands:
        print(f"+ {' '.join(command)}")
        completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
        if completed.returncode != 0:
            return completed.returncode

    print("Release gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
