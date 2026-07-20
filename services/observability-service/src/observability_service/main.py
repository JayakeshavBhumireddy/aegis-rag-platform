from __future__ import annotations

from aegis_shared.contracts import EventEnvelope, RequestContext
from fastapi import FastAPI
from pydantic import BaseModel, Field

from observability_service.settings import ObservabilitySettings
from observability_service.store_factory import build_observability_stores

SERVICE_VERSION = "observability-service-v0"

app = FastAPI(title="AegisRAG observability-service", version=SERVICE_VERSION)
STORES = build_observability_stores(ObservabilitySettings.from_env())


class AuditRecordRequest(BaseModel):
    request_context: RequestContext
    producer: str
    payload: dict


class AuditRecordResponse(BaseModel):
    event: EventEnvelope


class CostEventRequest(BaseModel):
    request_context: RequestContext
    producer: str
    tenant_id: str = Field(alias="tenantId")
    user_id: str = Field(alias="userId")
    route: str
    usage: dict
    metadata: dict = Field(default_factory=dict)


class CostEventResponse(BaseModel):
    event: EventEnvelope


class FeedbackEventRequest(BaseModel):
    request_context: RequestContext
    producer: str
    tenant_id: str = Field(alias="tenantId")
    user_id: str = Field(alias="userId")
    session_id: str = Field(alias="sessionId")
    message_id: str = Field(alias="messageId")
    rating: int = Field(ge=-1, le=1)
    comment: str | None = None
    categories: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class FeedbackEventResponse(BaseModel):
    event: EventEnvelope


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/audit/records", response_model=AuditRecordResponse)
def record(request: AuditRecordRequest) -> AuditRecordResponse:
    return AuditRecordResponse(
        event=STORES.audit_store.record(
            request_context=request.request_context,
            producer=request.producer,
            payload=request.payload,
        )
    )


@app.get("/v1/audit/records", response_model=list[EventEnvelope])
def list_records() -> list[EventEnvelope]:
    return STORES.audit_store.list_events()


@app.post("/v1/cost/events", response_model=CostEventResponse)
def record_cost(request: CostEventRequest) -> CostEventResponse:
    return CostEventResponse(
        event=STORES.cost_ledger.record(
            request_context=request.request_context,
            producer=request.producer,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            route=request.route,
            usage=request.usage,
            metadata=request.metadata,
        )
    )


@app.get("/v1/cost/events", response_model=list[EventEnvelope])
def list_cost_events() -> list[EventEnvelope]:
    return STORES.cost_ledger.list_events()


@app.post("/v1/feedback/events", response_model=FeedbackEventResponse)
def record_feedback(request: FeedbackEventRequest) -> FeedbackEventResponse:
    return FeedbackEventResponse(
        event=STORES.feedback_store.record(
            request_context=request.request_context,
            producer=request.producer,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            session_id=request.session_id,
            message_id=request.message_id,
            rating=request.rating,
            comment=request.comment,
            categories=request.categories,
            metadata=request.metadata,
        )
    )


@app.get("/v1/feedback/events", response_model=list[EventEnvelope])
def list_feedback_events() -> list[EventEnvelope]:
    return STORES.feedback_store.list_events()
