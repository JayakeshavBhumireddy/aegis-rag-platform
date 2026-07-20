from __future__ import annotations

import json

import pytest
from assistant_api.release_state import FALLBACK_RELEASE, load_active_release


def test_load_active_release_reads_promoted_metadata(tmp_path) -> None:
    path = tmp_path / "local-active.json"
    path.write_text(
        json.dumps(
            {
                "releaseId": "release_123",
                "status": "prod",
                "appVersion": "0.1.0",
                "contentVersion": "content-v1",
                "indexVersion": "index-v1",
                "promptVersion": "answer-prompt-v1",
                "policyVersion": "policy-baseline-v1",
                "guardrailVersion": "guardrails-local-v1",
                "routerConfigVersion": "inference-routes-v1",
                "extraField": "ignored",
            }
        ),
        encoding="utf-8",
    )

    active_release = load_active_release(path)

    assert active_release.release_id == "release_123"
    assert active_release.metadata["status"] == "prod"
    assert "extraField" not in active_release.metadata


def test_load_active_release_falls_back_when_no_active_release_exists(tmp_path) -> None:
    active_release = load_active_release(tmp_path / "missing.json")

    assert active_release.metadata == FALLBACK_RELEASE


def test_load_active_release_rejects_incomplete_metadata(tmp_path) -> None:
    path = tmp_path / "local-active.json"
    path.write_text(json.dumps({"releaseId": "release_123"}), encoding="utf-8")

    with pytest.raises(ValueError, match="missing fields"):
        load_active_release(path)
