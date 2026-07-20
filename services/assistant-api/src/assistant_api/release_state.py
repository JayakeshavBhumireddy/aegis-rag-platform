from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ACTIVE_RELEASE_PATH = ROOT / "data" / "processed" / "release-registry" / "local-active.json"

FALLBACK_RELEASE = {
    "releaseId": "local-unpromoted",
    "status": "unpromoted",
    "appVersion": "0.1.0",
    "contentVersion": "synthetic-enterprise-content-v1",
    "indexVersion": "local-index-unpromoted",
    "promptVersion": "answer-prompt-v1",
    "policyVersion": "policy-baseline-v1",
    "guardrailVersion": "guardrails-local-v1",
    "routerConfigVersion": "inference-routes-v1",
}

RELEASE_METADATA_FIELDS = (
    "releaseId",
    "status",
    "appVersion",
    "contentVersion",
    "indexVersion",
    "promptVersion",
    "policyVersion",
    "guardrailVersion",
    "routerConfigVersion",
)


@dataclass(frozen=True)
class ActiveRelease:
    metadata: dict[str, Any]

    @property
    def release_id(self) -> str:
        return str(self.metadata["releaseId"])


def load_active_release(path: Path | None = None) -> ActiveRelease:
    release_path = path or Path(
        os.getenv("AEGIS_ACTIVE_RELEASE_PATH", str(DEFAULT_ACTIVE_RELEASE_PATH))
    )
    if not release_path.exists():
        return ActiveRelease(metadata=dict(FALLBACK_RELEASE))
    release = json.loads(release_path.read_text(encoding="utf-8"))
    if not isinstance(release, dict):
        raise ValueError(f"active release metadata must be an object: {release_path}")
    return ActiveRelease(metadata=_release_metadata(release))


def _release_metadata(release: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in RELEASE_METADATA_FIELDS if field not in release]
    if missing:
        raise ValueError(f"active release metadata missing fields: {missing}")
    return {field: release[field] for field in RELEASE_METADATA_FIELDS}
