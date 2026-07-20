from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from aegis_shared.contracts import RetrievalResult, RetrievalScope
from reranker_service.ranker import rerank_candidates

from retrieval_service.index import DEFAULT_INDEX_DIR, search_local_hybrid_index

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CORPUS_PATH = ROOT / "data" / "raw" / "synthetic-enterprise" / "documents.json"
DEFAULT_CHUNKS_PATH = ROOT / "data" / "processed" / "synthetic-enterprise" / "chunks.json"


def load_documents(path: Path | None = None) -> list[dict[str, Any]]:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    if DEFAULT_CHUNKS_PATH.exists():
        return json.loads(DEFAULT_CHUNKS_PATH.read_text(encoding="utf-8"))
    return json.loads(DEFAULT_CORPUS_PATH.read_text(encoding="utf-8"))


def search_corpus(
    *,
    query: str,
    retrieval_scope: RetrievalScope,
    top_k: int = 20,
    retrieval_mode: str = "hybrid",
    documents: list[dict[str, Any]] | None = None,
) -> list[RetrievalResult]:
    docs = documents if documents is not None else load_documents()
    if documents is None:
        hybrid_results = search_local_hybrid_index(
            query=query,
            retrieval_scope=retrieval_scope,
            top_k=top_k,
            chunks=docs,
            index_dir=DEFAULT_INDEX_DIR,
        )
        if hybrid_results:
            return _finalize_results(
                query=query,
                results=hybrid_results,
                top_k=top_k,
                retrieval_mode=retrieval_mode,
            )

    terms = _terms(query)
    results: list[RetrievalResult] = []

    for doc in docs:
        if not _allowed(doc, retrieval_scope):
            continue

        metadata = _metadata(doc)
        haystack = " ".join(
            [
                _title(doc),
                str(metadata.get("moduleId", "")),
                str(metadata.get("requiredLicense", metadata.get("module", ""))),
                _text(doc),
            ]
        )
        score = _score(terms, haystack)
        if score <= 0:
            continue

        source_id = _source_id(doc)
        results.append(
            RetrievalResult(
                chunkId=_chunk_id(doc),
                sourceId=source_id,
                title=_title(doc),
                text=_text(doc),
                score=score,
                metadata={
                    "module": metadata.get("requiredLicense", metadata.get("module")),
                    "moduleId": metadata["moduleId"],
                    "trustLevel": metadata["trustLevel"],
                    "productVersion": metadata["productVersion"],
                    "requiredPermissions": metadata["requiredPermissions"],
                },
            )
        )

    return _finalize_results(
        query=query,
        results=sorted(results, key=lambda result: result.score, reverse=True),
        top_k=top_k,
        retrieval_mode=retrieval_mode,
    )


def _finalize_results(
    *,
    query: str,
    results: list[RetrievalResult],
    top_k: int,
    retrieval_mode: str,
) -> list[RetrievalResult]:
    if retrieval_mode in {"hybrid_rerank", "rerank"}:
        return rerank_candidates(query=query, candidates=results, top_k=top_k)
    return results[:top_k]


def _allowed(doc: dict[str, Any], scope: RetrievalScope) -> bool:
    metadata = _metadata(doc)
    required_permissions = set(metadata.get("requiredPermissions", []))
    return (
        metadata.get("trustLevel") == scope.trust_level
        and metadata.get("productVersion") == scope.product_version
        and metadata.get("requiredLicense", metadata.get("module")) in scope.modules
        and required_permissions.issubset(set(scope.permissions))
    )


def _metadata(doc: dict[str, Any]) -> dict[str, Any]:
    if "metadata" in doc:
        return dict(doc["metadata"])
    return {
        "module": doc["requiredLicense"],
        "moduleId": doc["moduleId"],
        "requiredLicense": doc["requiredLicense"],
        "requiredPermissions": doc["requiredPermissions"],
        "trustLevel": doc["trustLevel"],
        "productVersion": doc["productVersion"],
    }


def _source_id(doc: dict[str, Any]) -> str:
    return str(doc["sourceId"])


def _chunk_id(doc: dict[str, Any]) -> str:
    return str(doc.get("chunkId", f"{_source_id(doc)}#body"))


def _title(doc: dict[str, Any]) -> str:
    return str(doc["title"])


def _text(doc: dict[str, Any]) -> str:
    return str(doc.get("text", doc.get("body", "")))


def _terms(query: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2}


def _score(terms: set[str], haystack: str) -> float:
    words = _terms(haystack)
    if not terms:
        return 0.0
    matches = terms & words
    return round(len(matches) / len(terms), 4)
