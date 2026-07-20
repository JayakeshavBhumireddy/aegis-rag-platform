from __future__ import annotations

from typing import Any

from aegis_shared.contracts import EntitlementEnvelope, PolicyDecision, UiContext
from fastapi import FastAPI
from pydantic import BaseModel, Field

from context_service.builder import build_context_pack

SERVICE_VERSION = "context-service-v0"

app = FastAPI(title="AegisRAG context-service", version=SERVICE_VERSION)


class ContextBuildRequest(BaseModel):
    session_id: str = Field(alias="sessionId")
    message: str
    entitlement_envelope: EntitlementEnvelope = Field(alias="entitlementEnvelope")
    policy_decision: PolicyDecision = Field(alias="policyDecision")
    ui_context: UiContext | None = Field(alias="uiContext", default=None)


class ContextBuildResponse(BaseModel):
    context_pack: dict[str, Any] = Field(alias="contextPack")


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/context/build", response_model=ContextBuildResponse)
def build(request: ContextBuildRequest) -> ContextBuildResponse:
    return ContextBuildResponse(
        contextPack=build_context_pack(
            session_id=request.session_id,
            message=request.message,
            entitlement=request.entitlement_envelope,
            policy_decision=request.policy_decision,
            ui_context=request.ui_context,
        )
    )
