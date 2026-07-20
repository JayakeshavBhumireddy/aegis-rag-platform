from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from eval_service.release_registry import (
    build_local_release_candidate,
    promote_local_release_candidate,
    rollback_local_release,
    validate_release_metadata,
)


def test_builds_release_candidate_with_rollback_metadata(tmp_path) -> None:
    manifest_path = tmp_path / "index-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "indexVersion": "idx_123",
                "chunkerVersion": "chunker-v1",
                "embeddingModelVersion": "embedding-v1",
            }
        ),
        encoding="utf-8",
    )

    release = build_local_release_candidate(
        eval_result={
            "passed": True,
            "total": 1,
            "failures": [],
            "scores": {
                "licenseViolationRate": 0,
                "permissionViolationRate": 0,
                "piiLeakageRate": 0,
                "promptInjectionSuccessRate": 0,
                "costBudgetViolationRate": 0,
            },
            "results": [],
        },
        index_manifest_path=manifest_path,
        promoted_at=datetime(2026, 5, 8, tzinfo=UTC),
    )

    assert release["status"] == "candidate"
    assert release["indexVersion"] == "idx_123"
    assert release["chunkerVersion"] == "chunker-v1"
    assert release["embeddingModelVersion"] == "embedding-v1"
    assert release["scoreSummary"]["piiLeakageRate"] == 0
    assert release["rollback"]["indexVersion"] == "idx_123"


def test_rejects_release_candidate_when_eval_failed(tmp_path) -> None:
    manifest_path = tmp_path / "index-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "indexVersion": "idx_123",
                "chunkerVersion": "chunker-v1",
                "embeddingModelVersion": "embedding-v1",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="eval gate failed"):
        build_local_release_candidate(
            eval_result={"passed": False, "total": 1, "failures": ["case"], "results": []},
            index_manifest_path=manifest_path,
        )


def test_validates_required_rollback_fields() -> None:
    with pytest.raises(ValueError, match="rollback"):
        validate_release_metadata(
            {
                "releaseId": "release_1",
                "environment": "local",
                "appVersion": "0.1.0",
                "contentVersion": "content-v1",
                "indexVersion": "index-v1",
                "promptVersion": "answer-prompt-v1",
                "policyVersion": "policy-baseline-v1",
                "guardrailVersion": "guardrails-local-v1",
                "routerConfigVersion": "inference-routes-v1",
                "evalDatasetVersion": "synthetic-eval-v1",
                "evalRunId": "eval_1",
                "promotedAt": "2026-05-08T00:00:00Z",
                "status": "candidate",
                "eval": {"passed": True},
                "scoreSummary": {
                    "licenseViolationRate": 0,
                    "permissionViolationRate": 0,
                    "piiLeakageRate": 0,
                    "promptInjectionSuccessRate": 0,
                    "costBudgetViolationRate": 0,
                },
                "rollback": {"indexVersion": "index-v1"},
            }
        )


def test_validates_hard_gate_score_summary() -> None:
    release = {
        "releaseId": "release_1",
        "environment": "local",
        "appVersion": "0.1.0",
        "contentVersion": "content-v1",
        "indexVersion": "index-v1",
        "promptVersion": "answer-prompt-v1",
        "policyVersion": "policy-baseline-v1",
        "guardrailVersion": "guardrails-local-v1",
        "routerConfigVersion": "inference-routes-v1",
        "evalDatasetVersion": "synthetic-eval-v1",
        "evalRunId": "eval_1",
        "promotedAt": "2026-05-08T00:00:00Z",
        "status": "candidate",
        "eval": {"passed": True},
        "scoreSummary": {
            "licenseViolationRate": 0,
            "permissionViolationRate": 0,
            "piiLeakageRate": 1,
            "promptInjectionSuccessRate": 0,
            "costBudgetViolationRate": 0,
        },
        "rollback": {
            "serviceImage": "image",
            "promptVersion": "answer-prompt-v1",
            "policyVersion": "policy-baseline-v1",
            "indexVersion": "index-v1",
            "routerConfigVersion": "inference-routes-v1",
            "guardrailVersion": "guardrails-local-v1",
        },
    }

    with pytest.raises(ValueError, match="hard gate failed"):
        validate_release_metadata(release)


def test_validates_cost_budget_gate() -> None:
    release = {
        "releaseId": "release_1",
        "environment": "local",
        "appVersion": "0.1.0",
        "contentVersion": "content-v1",
        "indexVersion": "index-v1",
        "promptVersion": "answer-prompt-v1",
        "policyVersion": "policy-baseline-v1",
        "guardrailVersion": "guardrails-local-v1",
        "routerConfigVersion": "inference-routes-v1",
        "evalDatasetVersion": "synthetic-eval-v1",
        "evalRunId": "eval_1",
        "promotedAt": "2026-05-08T00:00:00Z",
        "status": "candidate",
        "eval": {"passed": True},
        "scoreSummary": {
            "licenseViolationRate": 0,
            "permissionViolationRate": 0,
            "piiLeakageRate": 0,
            "promptInjectionSuccessRate": 0,
            "costBudgetViolationRate": 1,
        },
        "rollback": {
            "serviceImage": "image",
            "promptVersion": "answer-prompt-v1",
            "policyVersion": "policy-baseline-v1",
            "indexVersion": "index-v1",
            "routerConfigVersion": "inference-routes-v1",
            "guardrailVersion": "guardrails-local-v1",
        },
    }

    with pytest.raises(ValueError, match="hard gate failed"):
        validate_release_metadata(release)


def test_promotes_local_candidate_to_active_release(tmp_path) -> None:
    candidate_path = tmp_path / "candidate.json"
    active_path = tmp_path / "active.json"
    rollback_path = tmp_path / "rollback.json"
    candidate = _release("release_1", status="candidate")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

    active = promote_local_release_candidate(
        candidate_path=candidate_path,
        active_path=active_path,
        previous_active_path=rollback_path,
        promoted_at=datetime(2026, 5, 9, tzinfo=UTC),
    )

    assert active["releaseId"] == "release_1"
    assert active["status"] == "prod"
    assert active["promotedAt"] == "2026-05-09T00:00:00Z"
    assert json.loads(active_path.read_text(encoding="utf-8"))["status"] == "prod"
    assert not rollback_path.exists()


def test_promoting_new_candidate_preserves_previous_active_for_rollback(tmp_path) -> None:
    candidate_path = tmp_path / "candidate.json"
    active_path = tmp_path / "active.json"
    rollback_path = tmp_path / "rollback.json"
    active_path.write_text(json.dumps(_release("release_1", status="prod")), encoding="utf-8")
    candidate_path.write_text(
        json.dumps(_release("release_2", status="candidate")),
        encoding="utf-8",
    )

    active = promote_local_release_candidate(
        candidate_path=candidate_path,
        active_path=active_path,
        previous_active_path=rollback_path,
        promoted_at=datetime(2026, 5, 9, tzinfo=UTC),
    )

    assert active["releaseId"] == "release_2"
    assert json.loads(rollback_path.read_text(encoding="utf-8"))["releaseId"] == "release_1"


def test_rolls_back_to_previous_active_release(tmp_path) -> None:
    active_path = tmp_path / "active.json"
    rollback_path = tmp_path / "rollback.json"
    active_path.write_text(json.dumps(_release("release_2", status="prod")), encoding="utf-8")
    rollback_path.write_text(json.dumps(_release("release_1", status="prod")), encoding="utf-8")

    active = rollback_local_release(
        active_path=active_path,
        rollback_path=rollback_path,
        rolled_back_at=datetime(2026, 5, 10, tzinfo=UTC),
    )

    assert active["releaseId"] == "release_1"
    assert active["status"] == "prod"
    assert json.loads(active_path.read_text(encoding="utf-8"))["releaseId"] == "release_1"
    rolled_back = json.loads(rollback_path.read_text(encoding="utf-8"))
    assert rolled_back["releaseId"] == "release_2"
    assert rolled_back["status"] == "rolled_back"
    assert rolled_back["rolledBackToReleaseId"] == "release_1"


def test_rejects_non_candidate_promotion(tmp_path) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(
        json.dumps(_release("release_1", status="prod")),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="only candidate"):
        promote_local_release_candidate(
            candidate_path=candidate_path,
            active_path=tmp_path / "active.json",
            previous_active_path=tmp_path / "rollback.json",
        )


def _release(release_id: str, *, status: str) -> dict:
    return {
        "releaseId": release_id,
        "environment": "local",
        "appVersion": "0.1.0",
        "serviceImage": "image",
        "contentVersion": "content-v1",
        "indexVersion": "index-v1",
        "promptVersion": "answer-prompt-v1",
        "policyVersion": "policy-baseline-v1",
        "guardrailVersion": "guardrails-local-v1",
        "routerConfigVersion": "inference-routes-v1",
        "evalDatasetVersion": "synthetic-eval-v1",
        "evalRunId": "eval_1",
        "promotedAt": "2026-05-08T00:00:00Z",
        "status": status,
        "eval": {"passed": True},
        "scoreSummary": {
            "licenseViolationRate": 0,
            "permissionViolationRate": 0,
            "piiLeakageRate": 0,
            "promptInjectionSuccessRate": 0,
            "costBudgetViolationRate": 0,
        },
        "rollback": {
            "serviceImage": "image",
            "promptVersion": "answer-prompt-v1",
            "policyVersion": "policy-baseline-v1",
            "indexVersion": "index-v1",
            "routerConfigVersion": "inference-routes-v1",
            "guardrailVersion": "guardrails-local-v1",
        },
    }
