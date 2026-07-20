"""Validate local runtime packaging files without requiring a Docker daemon."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "docker-compose.yml"
DOCKERFILE = ROOT / "infra" / "docker" / "python-service.Dockerfile"

EXPECTED_SERVICE_APPS = {
    "assistant_api.main:app",
    "auth_service.main:app",
    "context_service.main:app",
    "entitlement_service.main:app",
    "eval_service.main:app",
    "ingestion_service.main:app",
    "llm_gateway.main:app",
    "observability_service.main:app",
    "policy_service.main:app",
    "retrieval_service.main:app",
    "reranker_service.main:app",
    "verification_service.main:app",
}


def main() -> int:
    errors: list[str] = []
    compose_text = COMPOSE_FILE.read_text(encoding="utf-8")
    dockerfile_text = DOCKERFILE.read_text(encoding="utf-8")

    if "infra/docker/python-service.Dockerfile" not in compose_text:
        errors.append("docker-compose.yml does not reference the shared Python Dockerfile")
    if "AEGIS_ASSISTANT_DEPENDENCY_MODE: http" not in compose_text:
        errors.append("assistant-api is not configured for HTTP dependency mode in compose")
    if "python -m uvicorn ${AEGIS_SERVICE_APP}" not in dockerfile_text:
        errors.append("shared Dockerfile does not run AEGIS_SERVICE_APP with uvicorn")

    for service_app in sorted(EXPECTED_SERVICE_APPS):
        if f"AEGIS_SERVICE_APP: {service_app}" not in compose_text:
            errors.append(f"missing compose service app: {service_app}")

    docker = shutil.which("docker")
    if docker:
        completed = subprocess.run(
            [docker, "compose", "-f", str(COMPOSE_FILE), "config", "--quiet"],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode != 0:
            errors.append("docker compose config --quiet failed")

    if errors:
        print("Runtime packaging validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Runtime packaging validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
