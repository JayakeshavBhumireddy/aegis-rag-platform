from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from eval_service.runner import run_synthetic_eval

ROOT = Path(__file__).resolve().parents[4]
INDEX_MANIFEST_PATH = ROOT / "data" / "indexes" / "synthetic-enterprise" / "index-manifest.json"
RELEASE_REGISTRY_DIR = ROOT / "data" / "processed" / "release-registry"
LOCAL_CANDIDATE_PATH = RELEASE_REGISTRY_DIR / "local-candidate.json"
LOCAL_ACTIVE_PATH = RELEASE_REGISTRY_DIR / "local-active.json"
LOCAL_ROLLBACK_PATH = RELEASE_REGISTRY_DIR / "local-rollback.json"

REQUIRED_RELEASE_FIELDS = {
    "releaseId",
    "environment",
    "appVersion",
    "contentVersion",
    "indexVersion",
    "promptVersion",
    "policyVersion",
    "guardrailVersion",
    "routerConfigVersion",
    "evalDatasetVersion",
    "evalRunId",
    "promotedAt",
}
REQUIRED_ROLLBACK_FIELDS = {
    "serviceImage",
    "promptVersion",
    "policyVersion",
    "indexVersion",
    "routerConfigVersion",
    "guardrailVersion",
}


def build_local_release_candidate(
    *,
    eval_result: dict[str, Any] | None = None,
    index_manifest_path: Path = INDEX_MANIFEST_PATH,
    promoted_at: datetime | None = None,
) -> dict[str, Any]:
    result = eval_result if eval_result is not None else run_synthetic_eval()
    if not result.get("passed"):
        raise ValueError("cannot register release candidate when eval gate failed")

    index_manifest = json.loads(index_manifest_path.read_text(encoding="utf-8"))
    timestamp = promoted_at or datetime.now(UTC)
    release = {
        "releaseId": f"release-{timestamp.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
        "environment": "local",
        "appVersion": "0.1.0",
        "serviceImage": "aegis-rag-python-service:local",
        "contentVersion": "synthetic-enterprise-content-v1",
        "chunkerVersion": index_manifest["chunkerVersion"],
        "embeddingModelVersion": index_manifest["embeddingModelVersion"],
        "indexVersion": index_manifest["indexVersion"],
        "promptVersion": "answer-prompt-v1",
        "policyVersion": "policy-baseline-v1",
        "guardrailVersion": "guardrails-local-v1",
        "routerConfigVersion": "inference-routes-v1",
        "evalDatasetVersion": "synthetic-enterprise-eval-v1",
        "evalRunId": f"eval-{timestamp.strftime('%Y%m%d%H%M%S')}",
        "promotedAt": timestamp.isoformat().replace("+00:00", "Z"),
        "status": "candidate",
        "eval": result,
        "scoreSummary": result.get("scores", {}),
        "rollback": {
            "serviceImage": "aegis-rag-python-service:local",
            "promptVersion": "answer-prompt-v1",
            "policyVersion": "policy-baseline-v1",
            "indexVersion": index_manifest["indexVersion"],
            "routerConfigVersion": "inference-routes-v1",
            "guardrailVersion": "guardrails-local-v1",
        },
    }
    validate_release_metadata(release)
    return release


def write_local_release_candidate(
    *,
    output_path: Path = LOCAL_CANDIDATE_PATH,
) -> dict[str, Any]:
    release = build_local_release_candidate()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    return release


def promote_local_release_candidate(
    *,
    candidate_path: Path = LOCAL_CANDIDATE_PATH,
    active_path: Path = LOCAL_ACTIVE_PATH,
    previous_active_path: Path = LOCAL_ROLLBACK_PATH,
    promoted_at: datetime | None = None,
) -> dict[str, Any]:
    candidate = _read_release(candidate_path)
    validate_release_metadata(candidate)
    if candidate["status"] != "candidate":
        raise ValueError("only candidate releases can be promoted")

    if active_path.exists():
        previous_active = _read_release(active_path)
        validate_release_metadata(previous_active)
        previous_active_path.parent.mkdir(parents=True, exist_ok=True)
        previous_active_path.write_text(
            json.dumps(previous_active, indent=2) + "\n",
            encoding="utf-8",
        )

    timestamp = promoted_at or datetime.now(UTC)
    active_release = candidate | {
        "status": "prod",
        "promotedAt": timestamp.isoformat().replace("+00:00", "Z"),
    }
    validate_release_metadata(active_release)
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(json.dumps(active_release, indent=2) + "\n", encoding="utf-8")
    return active_release


def rollback_local_release(
    *,
    active_path: Path = LOCAL_ACTIVE_PATH,
    rollback_path: Path = LOCAL_ROLLBACK_PATH,
    rolled_back_at: datetime | None = None,
) -> dict[str, Any]:
    current_active = _read_release(active_path)
    validate_release_metadata(current_active)
    rollback_release = _read_release(rollback_path)
    validate_release_metadata(rollback_release)

    timestamp = rolled_back_at or datetime.now(UTC)
    rolled_back_current = current_active | {
        "status": "rolled_back",
        "rolledBackAt": timestamp.isoformat().replace("+00:00", "Z"),
        "rolledBackToReleaseId": rollback_release["releaseId"],
    }
    validate_release_metadata(rolled_back_current)
    rollback_active = rollback_release | {
        "status": "prod",
        "promotedAt": timestamp.isoformat().replace("+00:00", "Z"),
    }
    validate_release_metadata(rollback_active)

    rollback_path.write_text(
        json.dumps(rolled_back_current, indent=2) + "\n",
        encoding="utf-8",
    )
    active_path.write_text(json.dumps(rollback_active, indent=2) + "\n", encoding="utf-8")
    return rollback_active


def validate_release_metadata(release: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_RELEASE_FIELDS - set(release))
    if missing:
        raise ValueError(f"release metadata missing required fields: {missing}")
    rollback = release.get("rollback")
    if not isinstance(rollback, dict):
        raise ValueError("release metadata missing rollback object")
    missing_rollback = sorted(REQUIRED_ROLLBACK_FIELDS - set(rollback))
    if missing_rollback:
        raise ValueError(f"release rollback metadata missing fields: {missing_rollback}")
    if release.get("status") not in {"candidate", "staging", "canary", "prod", "rolled_back"}:
        raise ValueError("release status is invalid")
    if not release.get("eval", {}).get("passed"):
        raise ValueError("release eval gate did not pass")
    scores = release.get("scoreSummary", {})
    for hard_gate in (
        "licenseViolationRate",
        "permissionViolationRate",
        "piiLeakageRate",
        "promptInjectionSuccessRate",
        "costBudgetViolationRate",
    ):
        if scores.get(hard_gate, 0) != 0:
            raise ValueError(f"release hard gate failed: {hard_gate}")


def _read_release(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"release metadata not found: {path}")
    release = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(release, dict):
        raise ValueError(f"release metadata must be an object: {path}")
    return release


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage local AegisRAG release metadata.")
    parser.add_argument(
        "command",
        choices=("candidate", "promote", "rollback"),
        nargs="?",
        default="candidate",
    )
    args = parser.parse_args(argv)
    if args.command == "candidate":
        release = write_local_release_candidate()
    elif args.command == "promote":
        release = promote_local_release_candidate()
    else:
        release = rollback_local_release()
    print(json.dumps(release, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
