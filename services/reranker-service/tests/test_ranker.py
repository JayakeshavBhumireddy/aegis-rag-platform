from __future__ import annotations

from aegis_shared.contracts import RetrievalResult
from fastapi.testclient import TestClient
from reranker_service.main import app
from reranker_service.ranker import rerank_candidates


def test_rerank_candidates_prefers_query_specific_approved_content() -> None:
    results = rerank_candidates(
        query="monthly billing submission",
        candidates=[
            _candidate(
                chunk_id="reports",
                title="Reports overview",
                text="Open reports dashboards and exports.",
                score=0.7,
                module="Reports",
            ),
            _candidate(
                chunk_id="billing",
                title="Monthly Billing Submission",
                text="Submit monthly billing from the Billing workspace.",
                score=0.5,
                module="Billing",
            ),
        ],
        top_k=2,
    )

    assert [result.chunk_id for result in results] == ["billing", "reports"]
    assert results[0].metadata["reranker"]["model"] == "local-lexical-reranker-v1"
    assert results[0].metadata["reranker"]["inputScore"] == 0.5


def test_rerank_endpoint_returns_top_k_results_with_aliases() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/rerank",
        json={
            "query": "billing submission",
            "topK": 1,
            "candidates": [
                _candidate(
                    chunk_id="reports",
                    title="Reports",
                    text="Open reports dashboards.",
                    score=0.9,
                    module="Reports",
                ).model_dump(by_alias=True),
                _candidate(
                    chunk_id="billing",
                    title="Billing Submission",
                    text="Submit monthly billing.",
                    score=0.4,
                    module="Billing",
                ).model_dump(by_alias=True),
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert [result["chunkId"] for result in body["results"]] == ["billing"]


def _candidate(
    *,
    chunk_id: str,
    title: str,
    text: str,
    score: float,
    module: str,
) -> RetrievalResult:
    return RetrievalResult(
        chunkId=chunk_id,
        sourceId=f"source-{chunk_id}",
        title=title,
        text=text,
        score=score,
        metadata={"module": module, "trustLevel": "approved"},
    )
