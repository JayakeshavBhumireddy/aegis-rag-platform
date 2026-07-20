from __future__ import annotations

from aegis_shared.contracts import RetrievalResult, RetrievalScope
from fastapi import FastAPI
from pydantic import BaseModel, Field

from retrieval_service.search import search_corpus

SERVICE_VERSION = "retrieval-service-v0"

app = FastAPI(title="AegisRAG retrieval-service", version=SERVICE_VERSION)


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    retrieval_scope: RetrievalScope = Field(alias="retrievalScope")
    top_k: int = Field(alias="topK", default=20, ge=1, le=100)
    retrieval_mode: str = Field(alias="retrievalMode", default="hybrid")


class RetrievalSearchResponse(BaseModel):
    results: list[RetrievalResult]


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/retrieval/search", response_model=RetrievalSearchResponse)
def search(request: RetrievalSearchRequest) -> RetrievalSearchResponse:
    return RetrievalSearchResponse(
        results=search_corpus(
            query=request.query,
            retrieval_scope=request.retrieval_scope,
            top_k=request.top_k,
            retrieval_mode=request.retrieval_mode,
        )
    )
