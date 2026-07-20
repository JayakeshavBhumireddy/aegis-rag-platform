from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DataAccessMode(StrEnum):
    PRODUCT_GUIDANCE_ONLY = "product_guidance_only"
    SECURE_CUSTOMER_DATA = "secure_customer_data"
    DISABLED = "disabled"


class PolicyDecisionValue(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


class ExpectedBehavior(StrEnum):
    ANSWER = "answer"
    DENY = "deny"
    ESCALATE = "escalate"
    ASK_CLARIFYING_QUESTION = "ask_clarifying_question"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    ENTITLEMENT_UNAVAILABLE = "ENTITLEMENT_UNAVAILABLE"
    POLICY_DENIED = "POLICY_DENIED"
    PII_BLOCKED = "PII_BLOCKED"
    RETRIEVAL_EMPTY = "RETRIEVAL_EMPTY"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


class EventType(StrEnum):
    INGESTION_REQUESTED = "aegis.ingestion.requested"
    INDEX_BUILD_COMPLETED = "aegis.index.build.completed"
    EVAL_RUN_COMPLETED = "aegis.eval.run.completed"
    FEEDBACK_RECEIVED = "aegis.feedback.received"
    AUDIT_RECORD_CREATED = "aegis.audit.record.created"
    COST_EVENT_RECORDED = "aegis.cost.event.recorded"
    RELEASE_PROMOTED = "aegis.release.promoted"


class UiContext(BaseModel):
    module: str | None = None
    page: str | None = None
    action: str | None = None
    locale: str | None = None


class RequestContext(BaseModel):
    request_id: str = Field(alias="requestId")
    trace_id: str = Field(alias="traceId")
    timestamp: datetime
    caller: str
    contract_version: str = Field(alias="contractVersion", default="v1")


class AuthenticatedPrincipal(BaseModel):
    subject: str
    tenant_id: str = Field(alias="tenantId")
    user_id: str = Field(alias="userId")
    roles: list[str] = Field(default_factory=list)
    issuer: str


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    retryable: bool
    safe_user_message: str = Field(alias="safeUserMessage")
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    status: str = "error"
    error: ErrorDetail


class EventEnvelope(BaseModel):
    event_id: str = Field(alias="eventId")
    event_type: EventType = Field(alias="eventType")
    event_version: str = Field(alias="eventVersion", default="v1")
    occurred_at: datetime = Field(alias="occurredAt")
    request_id: str = Field(alias="requestId")
    trace_id: str = Field(alias="traceId")
    producer: str
    payload: dict[str, Any] = Field(default_factory=dict)


class EntitlementEnvelope(BaseModel):
    tenant_id: str = Field(alias="tenantId")
    user_id: str = Field(alias="userId")
    region: str
    product_version: str = Field(alias="productVersion")
    licensed_modules: list[str] = Field(alias="licensedModules")
    enabled_features: list[str] = Field(alias="enabledFeatures")
    role: str
    permissions: list[str]
    license_hash: str = Field(alias="licenseHash")
    permission_hash: str = Field(alias="permissionHash")
    data_access_mode: DataAccessMode = Field(alias="dataAccessMode")


class RetrievalScope(BaseModel):
    tenant_id: str = Field(alias="tenantId")
    modules: list[str]
    permissions: list[str]
    product_version: str = Field(alias="productVersion")
    trust_level: str = Field(alias="trustLevel", default="approved")
    region: str | None = None


class PolicyDecision(BaseModel):
    decision: PolicyDecisionValue
    can_retrieve: bool = Field(alias="canRetrieve")
    can_answer: bool = Field(alias="canAnswer")
    can_cache: bool = Field(alias="canCache")
    must_escalate: bool = Field(alias="mustEscalate")
    retrieval_scope: RetrievalScope | None = Field(alias="retrievalScope", default=None)
    reasons: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    source_id: str = Field(alias="sourceId")
    chunk_id: str = Field(alias="chunkId")
    title: str
    url: str | None = None


class RetrievalResult(BaseModel):
    chunk_id: str = Field(alias="chunkId")
    source_id: str = Field(alias="sourceId")
    title: str
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RerankRequest(BaseModel):
    query: str = Field(min_length=1)
    candidates: list[RetrievalResult]
    top_k: int = Field(alias="topK", default=20, ge=1, le=100)


class RerankResponse(BaseModel):
    results: list[RetrievalResult]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    tenant_id: str = Field(alias="tenantId")
    user_id: str = Field(alias="userId")
    session_id: str = Field(alias="sessionId")
    ui_context: UiContext | None = Field(alias="uiContext", default=None)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    route: str
    escalation: dict[str, Any] | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    release_metadata: dict[str, Any] = Field(alias="releaseMetadata", default_factory=dict)


class VerificationResult(BaseModel):
    verified: bool
    grounded: bool
    citations_valid: bool = Field(alias="citationsValid")
    permission_compliant: bool = Field(alias="permissionCompliant")
    pii_safe: bool = Field(alias="piiSafe")
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)


class EvalCase(BaseModel):
    id: str
    question: str
    tenant_context: dict[str, Any] = Field(alias="tenantContext")
    expected_behavior: ExpectedBehavior = Field(alias="expectedBehavior")
    expected_modules: list[str] = Field(alias="expectedModules", default_factory=list)
    forbidden_content: list[str] = Field(alias="forbiddenContent", default_factory=list)
    must_cite_source: bool = Field(alias="mustCiteSource", default=True)
    risk_level: RiskLevel = Field(alias="riskLevel")
