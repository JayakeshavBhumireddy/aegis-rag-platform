from __future__ import annotations

from aegis_shared.contracts import EntitlementEnvelope, PolicyDecision, RiskLevel
from fastapi import FastAPI
from pydantic import BaseModel, Field

from policy_service.evaluator import evaluate_policy

SERVICE_VERSION = "policy-service-v0"

app = FastAPI(title="AegisRAG policy-service", version=SERVICE_VERSION)


class PolicyEvaluateRequest(BaseModel):
    entitlement_envelope: EntitlementEnvelope = Field(alias="entitlementEnvelope")
    intent: str
    risk: RiskLevel = RiskLevel.LOW
    requested_module: str | None = Field(alias="requestedModule", default=None)
    requested_permissions: list[str] = Field(alias="requestedPermissions", default_factory=list)


class PolicyEvaluateResponse(BaseModel):
    policy_decision: PolicyDecision = Field(alias="policyDecision")


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/policy/evaluate", response_model=PolicyEvaluateResponse)
def evaluate(request: PolicyEvaluateRequest) -> PolicyEvaluateResponse:
    return PolicyEvaluateResponse(
        policyDecision=evaluate_policy(
            entitlement=request.entitlement_envelope,
            intent=request.intent,
            risk=request.risk,
            requested_module=request.requested_module,
            requested_permissions=request.requested_permissions,
        )
    )
