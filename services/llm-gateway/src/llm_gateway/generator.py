from __future__ import annotations

from aegis_shared.contracts import Citation, RetrievalResult


def generate_answer(
    *, message: str, retrieval_results: list[RetrievalResult]
) -> tuple[str, list[Citation], float]:
    if not retrieval_results:
        return (
            "I could not find approved context that matches your request.",
            [],
            0.0,
        )

    top = retrieval_results[0]
    citation = Citation(
        sourceId=top.source_id,
        chunkId=top.chunk_id,
        title=top.title,
        url=None,
    )
    return top.text, [citation], min(0.95, max(0.5, top.score))
