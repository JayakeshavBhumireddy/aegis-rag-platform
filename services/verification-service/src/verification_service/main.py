from __future__ import annotations

from aegis_shared.contracts import Citation, PolicyDecision, RetrievalResult, VerificationResult
from fastapi import FastAPI
from pydantic import BaseModel

from verification_service.verifier import verify_answer

SERVICE_VERSION = "verification-service-v0"

app = FastAPI(title="AegisRAG verification-service", version=SERVICE_VERSION)


class VerificationRequest(BaseModel):
    answer: str
    citations: list[Citation]
    retrieval_results: list[RetrievalResult]
    policy_decision: PolicyDecision


class VerificationResponse(BaseModel):
    verification: VerificationResult


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/verification/check", response_model=VerificationResponse)
def check(request: VerificationRequest) -> VerificationResponse:
    return VerificationResponse(
        verification=verify_answer(
            answer=request.answer,
            citations=request.citations,
            retrieval_results=request.retrieval_results,
            policy_decision=request.policy_decision,
        )
    )
