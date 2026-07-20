from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from aegis_shared.contracts import RetrievalResult, RetrievalScope

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_INDEX_DIR = ROOT / "data" / "indexes" / "synthetic-enterprise"
KEYWORD_INDEX_NAME = "keyword-index.json"
VECTOR_INDEX_NAME = "vector-index.json"
HYBRID_MANIFEST_NAME = "index-manifest.json"
EMBEDDING_DIMENSIONS = 16


def publish_local_hybrid_index(
    *,
    chunks: list[dict[str, Any]],
    index_dir: Path = DEFAULT_INDEX_DIR,
) -> dict[str, Any]:
    keyword_index = _build_keyword_index(chunks)
    vector_index = _build_vector_index(chunks)
    index_dir.mkdir(parents=True, exist_ok=True)
    _write_json(index_dir / KEYWORD_INDEX_NAME, keyword_index)
    _write_json(index_dir / VECTOR_INDEX_NAME, vector_index)

    index_version = _index_version(chunks)
    manifest = {
        "version": "synthetic-enterprise-index-v1",
        "indexVersion": index_version,
        "indexType": "local_hybrid",
        "keywordProvider": "local_keyword",
        "keywordIndexPath": str(index_dir / KEYWORD_INDEX_NAME),
        "vectorProvider": "local_hash_vector",
        "vectorIndexPath": str(index_dir / VECTOR_INDEX_NAME),
        "embeddingModelVersion": "hashing-vector-v1",
        "embeddingDimensions": EMBEDDING_DIMENSIONS,
        "chunkerVersion": "synthetic-single-body-v1",
        "chunkCount": len(chunks),
        "sourceIds": sorted({chunk["sourceId"] for chunk in chunks}),
        "chunks": [
            {
                "chunkId": chunk["chunkId"],
                "sourceId": chunk["sourceId"],
                "checksum": chunk["checksum"],
                "metadata": chunk["metadata"],
            }
            for chunk in chunks
        ],
    }
    _write_json(index_dir / HYBRID_MANIFEST_NAME, manifest)
    return manifest


def search_local_hybrid_index(
    *,
    query: str,
    retrieval_scope: RetrievalScope,
    top_k: int,
    chunks: list[dict[str, Any]],
    index_dir: Path = DEFAULT_INDEX_DIR,
) -> list[RetrievalResult]:
    keyword_index_path = index_dir / KEYWORD_INDEX_NAME
    vector_index_path = index_dir / VECTOR_INDEX_NAME
    if not keyword_index_path.exists() or not vector_index_path.exists():
        return []

    keyword_index = _read_json(keyword_index_path)
    vector_index = _read_json(vector_index_path)
    chunk_by_id = {chunk["chunkId"]: chunk for chunk in chunks}
    query_terms = _terms(query)
    query_vector = embed_text(query)
    scored: dict[str, float] = {}

    for term in query_terms:
        for chunk_id, term_score in keyword_index.get("postings", {}).get(term, {}).items():
            scored[chunk_id] = scored.get(chunk_id, 0.0) + float(term_score)

    for chunk_id, vector in vector_index.get("vectors", {}).items():
        scored[chunk_id] = scored.get(chunk_id, 0.0) + cosine_similarity(query_vector, vector)

    results: list[RetrievalResult] = []
    for chunk_id, score in scored.items():
        chunk = chunk_by_id.get(chunk_id)
        if chunk is None or not _allowed(chunk, retrieval_scope):
            continue
        metadata = dict(chunk["metadata"])
        results.append(
            RetrievalResult(
                chunkId=chunk["chunkId"],
                sourceId=chunk["sourceId"],
                title=chunk["title"],
                text=chunk["text"],
                score=round(score, 4),
                metadata={
                    "module": metadata.get("requiredLicense", metadata.get("module")),
                    "moduleId": metadata["moduleId"],
                    "trustLevel": metadata["trustLevel"],
                    "productVersion": metadata["productVersion"],
                    "requiredPermissions": metadata["requiredPermissions"],
                    "retrievalMode": "local_hybrid",
                },
            )
        )

    return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]


def embed_text(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for term in _terms(text):
        digest = hashlib.sha256(term.encode("utf-8")).digest()
        bucket = digest[0] % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[1] % 2 == 0 else -1.0
        vector[bucket] += sign
    return _normalize(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))


def _build_keyword_index(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    postings: dict[str, dict[str, float]] = {}
    for chunk in chunks:
        terms = _terms(" ".join([chunk["title"], chunk["text"], chunk["metadata"]["moduleId"]]))
        for term in terms:
            postings.setdefault(term, {})[chunk["chunkId"]] = 1.0
    return {"version": "local-keyword-v1", "postings": postings}


def _build_vector_index(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": "local-hash-vector-v1",
        "dimensions": EMBEDDING_DIMENSIONS,
        "vectors": {chunk["chunkId"]: embed_text(chunk["text"]) for chunk in chunks},
    }


def _allowed(chunk: dict[str, Any], scope: RetrievalScope) -> bool:
    metadata = chunk["metadata"]
    required_permissions = set(metadata.get("requiredPermissions", []))
    return (
        metadata.get("trustLevel") == scope.trust_level
        and metadata.get("productVersion") == scope.product_version
        and metadata.get("requiredLicense", metadata.get("module")) in scope.modules
        and required_permissions.issubset(set(scope.permissions))
    )


def _index_version(chunks: list[dict[str, Any]]) -> str:
    chunk_hashes = [chunk["checksum"] for chunk in chunks]
    return hashlib.sha256("\n".join(sorted(chunk_hashes)).encode("utf-8")).hexdigest()


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", value.lower()) if len(term) > 2}


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [round(value / magnitude, 6) for value in vector]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
