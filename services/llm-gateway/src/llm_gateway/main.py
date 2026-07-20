from __future__ import annotations

from aegis_shared.contracts import Citation, RetrievalResult
from fastapi import FastAPI
from pydantic import BaseModel

from llm_gateway.generator import generate_answer

SERVICE_VERSION = "llm-gateway-v0"

app = FastAPI(title="AegisRAG llm-gateway", version=SERVICE_VERSION)


class GenerateRequest(BaseModel):
    message: str
    retrieval_results: list[RetrievalResult]


class GenerateResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    provider: str = "local-deterministic"
    model: str = "synthetic-context-extractor-v0"


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/llm/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    answer, citations, confidence = generate_answer(
        message=request.message,
        retrieval_results=request.retrieval_results,
    )
    return GenerateResponse(answer=answer, citations=citations, confidence=confidence)
