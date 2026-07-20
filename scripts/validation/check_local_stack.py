"""Check health endpoints for a running local AegisRAG docker compose stack."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

HEALTH_ENDPOINTS = {
    "assistant-api": "http://localhost:8000/health/ready",
    "auth-service": "http://localhost:8010/health/ready",
    "entitlement-service": "http://localhost:8011/health/ready",
    "policy-service": "http://localhost:8012/health/ready",
    "context-service": "http://localhost:8013/health/ready",
    "retrieval-service": "http://localhost:8014/health/ready",
    "llm-gateway": "http://localhost:8015/health/ready",
    "verification-service": "http://localhost:8016/health/ready",
    "observability-service": "http://localhost:8017/health/ready",
    "ingestion-service": "http://localhost:8018/health/ready",
    "eval-service": "http://localhost:8019/health/ready",
}


def main() -> int:
    failures: list[str] = []
    for service, url in HEALTH_ENDPOINTS.items():
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
            failures.append(f"{service}: {exc}")
            continue
        if body.get("status") != "ok":
            failures.append(f"{service}: unexpected health body {body}")

    if failures:
        print("Local stack health check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Local stack health check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
