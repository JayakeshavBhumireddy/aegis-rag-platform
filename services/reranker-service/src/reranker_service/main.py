from __future__ import annotations

from aegis_shared.contracts import RerankRequest, RerankResponse
from fastapi import FastAPI

from reranker_service.ranker import rerank_candidates

SERVICE_VERSION = "reranker-service-v0"

app = FastAPI(title="AegisRAG reranker-service", version=SERVICE_VERSION)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/rerank", response_model=RerankResponse)
def rerank(request: RerankRequest) -> RerankResponse:
    return RerankResponse(
        results=rerank_candidates(
            query=request.query,
            candidates=request.candidates,
            top_k=request.top_k,
        )
    )
