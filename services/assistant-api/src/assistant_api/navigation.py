from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from aegis_shared.contracts import RetrievalResult, RetrievalScope
from retrieval_service.search import DEFAULT_CORPUS_PATH

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MODULES_PATH = ROOT / "data" / "raw" / "synthetic-enterprise" / "modules.json"


def load_modules(path: Path = DEFAULT_MODULES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_navigation_route(
    *,
    query: str,
    retrieval_scope: RetrievalScope,
    modules: list[dict[str, Any]] | None = None,
    documents: list[dict[str, Any]] | None = None,
) -> RetrievalResult | None:
    module_defs = modules if modules is not None else load_modules()
    docs = documents if documents is not None else json.loads(DEFAULT_CORPUS_PATH.read_text())
    query_terms = _terms(query)

    best: tuple[float, dict[str, Any], dict[str, Any]] | None = None
    for module in module_defs:
        if module["requiredLicense"] not in retrieval_scope.modules:
            continue
        for route in module["routes"]:
            required_permissions = set(route["requiredPermissions"])
            if not required_permissions.issubset(set(retrieval_scope.permissions)):
                continue
            route_terms = _terms(" ".join([module["name"], route["screen"], *route["path"]]))
            score = len(query_terms & route_terms) / max(len(query_terms), 1)
            if score <= 0:
                continue
            if best is None or score > best[0]:
                best = (score, module, route)

    if best is None:
        return None

    score, module, route = best
    doc = _document_for_route(docs, route["routeId"])
    if doc is None:
        return None

    source_id = str(doc["sourceId"])
    return RetrievalResult(
        chunkId=f"{source_id}#navigation",
        sourceId=source_id,
        title=f"{route['screen']} Navigation",
        text=f"To open {route['screen']}, go to {' > '.join(route['path'])}.",
        score=round(score, 4),
        metadata={
            "module": module["requiredLicense"],
            "moduleId": module["moduleId"],
            "routeId": route["routeId"],
            "trustLevel": doc["trustLevel"],
            "productVersion": doc["productVersion"],
            "requiredPermissions": route["requiredPermissions"],
        },
    )


def _document_for_route(docs: list[dict[str, Any]], route_id: str) -> dict[str, Any] | None:
    expected_source_id = f"doc_{route_id.replace('.', '_')}"
    for doc in docs:
        if doc.get("sourceId") == expected_source_id:
            return doc
    return None


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", value.lower()) if len(term) > 2}
