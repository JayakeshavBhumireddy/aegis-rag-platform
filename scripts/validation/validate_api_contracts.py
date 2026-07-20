"""Validate implemented FastAPI routes against the API surface manifest."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[2]
API_SURFACE_PATH = ROOT / "docs" / "architecture" / "api-surface-v1.json"
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
    for entry in reversed(PYTHONPATH_ENTRIES):
        sys.path.insert(0, str(ROOT / entry))
    os.environ.setdefault("AEGIS_AUTH_DEV_SECRET", "aegis-local-dev-secret")

    manifest = json.loads(API_SURFACE_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    for service_name, service in sorted(manifest["services"].items()):
        errors.extend(_validate_service(service_name, service))

    if errors:
        print("API contract validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("API contract validation passed.")
    return 0


def _validate_service(service_name: str, service: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    app_import = service.get("app")
    if not isinstance(app_import, str) or ":" not in app_import:
        return [f"{service_name}: invalid app import {app_import!r}"]
    app = _load_app(app_import)
    implemented = _implemented_routes(app)
    expected = {
        (route["method"], route["path"])
        for route in service.get("routes", [])
        if isinstance(route, dict)
    }
    missing = sorted(expected - implemented)
    unexpected = sorted(
        route
        for route in implemented - expected
        if route[1].startswith("/v1/") or route[1].startswith("/health/")
    )
    if missing:
        errors.append(f"{service_name}: missing routes {missing}")
    if unexpected:
        errors.append(f"{service_name}: undocumented routes {unexpected}")
    if ("GET", "/health/live") not in implemented:
        errors.append(f"{service_name}: missing live health endpoint")
    if ("GET", "/health/ready") not in implemented:
        errors.append(f"{service_name}: missing ready health endpoint")
    return errors


def _load_app(app_import: str) -> Any:
    module_name, attribute = app_import.split(":", maxsplit=1)
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def _implemented_routes(app: Any) -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or set():
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes.add((method, route.path))
    return routes


if __name__ == "__main__":
    sys.exit(main())
