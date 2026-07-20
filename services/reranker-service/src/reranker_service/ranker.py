from __future__ import annotations

import re
from typing import Any

from aegis_shared.contracts import RetrievalResult


def rerank_candidates(
    *,
    query: str,
    candidates: list[RetrievalResult],
    top_k: int = 20,
) -> list[RetrievalResult]:
    scored = [
        _reranked_candidate(query=query, candidate=candidate, ordinal=ordinal)
        for ordinal, candidate in enumerate(candidates)
    ]
    scored.sort(
        key=lambda item: (
            item["score"],
            item["signals"]["queryTermCoverage"],
            -item["ordinal"],
        ),
        reverse=True,
    )
    return [item["candidate"] for item in scored[:top_k]]


def _reranked_candidate(
    *,
    query: str,
    candidate: RetrievalResult,
    ordinal: int,
) -> dict[str, Any]:
    signals = _ranking_signals(query=query, candidate=candidate)
    base_score = max(candidate.score, 0.0)
    score = round(
        (base_score * 0.55)
        + (signals["queryTermCoverage"] * 0.25)
        + (signals["titleTermCoverage"] * 0.1)
        + signals["moduleBoost"]
        + signals["trustBoost"],
        4,
    )
    enriched = candidate.model_copy(
        update={
            "score": score,
            "metadata": {
                **candidate.metadata,
                "reranker": {
                    "model": "local-lexical-reranker-v1",
                    "inputScore": candidate.score,
                    "signals": signals,
                },
            },
        }
    )
    return {"candidate": enriched, "score": score, "signals": signals, "ordinal": ordinal}


def _ranking_signals(*, query: str, candidate: RetrievalResult) -> dict[str, float]:
    query_terms = _terms(query)
    text_terms = _terms(" ".join([candidate.title, candidate.text]))
    title_terms = _terms(candidate.title)
    module_terms = _terms(str(candidate.metadata.get("module", "")))
    return {
        "queryTermCoverage": _coverage(query_terms, text_terms),
        "titleTermCoverage": _coverage(query_terms, title_terms),
        "moduleBoost": 0.05 if query_terms & module_terms else 0.0,
        "trustBoost": 0.05 if candidate.metadata.get("trustLevel") == "approved" else 0.0,
    }


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", value.lower()) if len(term) > 2}


def _coverage(query_terms: set[str], candidate_terms: set[str]) -> float:
    if not query_terms:
        return 0.0
    return round(len(query_terms & candidate_terms) / len(query_terms), 4)
