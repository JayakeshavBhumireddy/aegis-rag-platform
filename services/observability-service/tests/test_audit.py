from __future__ import annotations

from aegis_shared.contracts import EventType
from aegis_shared.runtime import new_request_context
from fastapi.testclient import TestClient
from observability_service.audit import InMemoryAuditStore
from observability_service.costs import GLOBAL_COST_LEDGER, InMemoryCostLedger
from observability_service.feedback import GLOBAL_FEEDBACK_STORE, InMemoryFeedbackStore
from observability_service.main import app


def test_in_memory_audit_store_records_event_envelope() -> None:
    store = InMemoryAuditStore()
    context = new_request_context(caller="assistant-api", request_id="req_audit")

    event = store.record(
        request_context=context,
        producer="assistant-api",
        payload={"stage": "policy_evaluated"},
    )

    assert event.event_type == EventType.AUDIT_RECORD_CREATED
    assert event.request_id == "req_audit"
    assert event.payload["stage"] == "policy_evaluated"
    assert store.list_events() == [event]


def test_observability_api_records_audit_event() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/audit/records",
        json={
            "request_context": {
                "requestId": "req_api",
                "traceId": "trace_api",
                "timestamp": "2026-05-08T00:00:00Z",
                "caller": "assistant-api",
                "contractVersion": "v1",
            },
            "producer": "assistant-api",
            "payload": {"stage": "request_received"},
        },
    )

    assert response.status_code == 200
    body = response.json()["event"]
    assert body["eventType"] == "aegis.audit.record.created"
    assert body["requestId"] == "req_api"


def test_in_memory_cost_ledger_records_cost_event() -> None:
    ledger = InMemoryCostLedger()
    context = new_request_context(caller="assistant-api", request_id="req_cost")

    event = ledger.record(
        request_context=context,
        producer="assistant-api",
        tenant_id="tenant_123",
        user_id="user_123",
        route="navigation_graph",
        usage={"estimatedCostUsd": 0.0001, "currency": "USD"},
        metadata={"citationCount": 1},
    )

    assert event.event_type == EventType.COST_EVENT_RECORDED
    assert event.request_id == "req_cost"
    assert event.payload["route"] == "navigation_graph"
    assert event.payload["usage"]["estimatedCostUsd"] == 0.0001
    assert ledger.list_events() == [event]


def test_observability_api_records_cost_event() -> None:
    GLOBAL_COST_LEDGER.clear()
    client = TestClient(app)

    response = client.post(
        "/v1/cost/events",
        json={
            "request_context": {
                "requestId": "req_cost_api",
                "traceId": "trace_cost_api",
                "timestamp": "2026-05-08T00:00:00Z",
                "caller": "assistant-api",
                "contractVersion": "v1",
            },
            "producer": "assistant-api",
            "tenantId": "tenant_123",
            "userId": "user_123",
            "route": "navigation_graph",
            "usage": {"estimatedCostUsd": 0.0001, "currency": "USD"},
            "metadata": {"citationCount": 1},
        },
    )

    assert response.status_code == 200
    body = response.json()["event"]
    assert body["eventType"] == "aegis.cost.event.recorded"
    assert body["requestId"] == "req_cost_api"


def test_in_memory_feedback_store_records_feedback_event() -> None:
    store = InMemoryFeedbackStore()
    context = new_request_context(caller="assistant-api", request_id="req_feedback")

    event = store.record(
        request_context=context,
        producer="assistant-ui",
        tenant_id="tenant_123",
        user_id="user_123",
        session_id="session_123",
        message_id="message_123",
        rating=1,
        comment="Helpful answer.",
        categories=["grounded"],
    )

    assert event.event_type == EventType.FEEDBACK_RECEIVED
    assert event.request_id == "req_feedback"
    assert event.payload["rating"] == 1
    assert event.payload["categories"] == ["grounded"]
    assert store.list_events() == [event]


def test_observability_api_records_feedback_event() -> None:
    GLOBAL_FEEDBACK_STORE.clear()
    client = TestClient(app)

    response = client.post(
        "/v1/feedback/events",
        json={
            "request_context": {
                "requestId": "req_feedback_api",
                "traceId": "trace_feedback_api",
                "timestamp": "2026-05-08T00:00:00Z",
                "caller": "assistant-ui",
                "contractVersion": "v1",
            },
            "producer": "assistant-ui",
            "tenantId": "tenant_123",
            "userId": "user_123",
            "sessionId": "session_123",
            "messageId": "message_123",
            "rating": -1,
            "comment": "Citation was missing.",
            "categories": ["citation_issue"],
            "metadata": {"route": "scoped_rag_local"},
        },
    )

    assert response.status_code == 200
    body = response.json()["event"]
    assert body["eventType"] == "aegis.feedback.received"
    assert body["payload"]["rating"] == -1
    assert body["payload"]["categories"] == ["citation_issue"]
