from __future__ import annotations

from aegis_shared.contracts import EventType
from aegis_shared.runtime import new_request_context
from observability_service.event_repository import SQLiteEventEnvelopeRepository
from observability_service.settings import ObservabilitySettings
from observability_service.store_factory import build_observability_stores


def test_sqlite_observability_stores_persist_event_envelopes(tmp_path) -> None:
    db_path = tmp_path / "observability.db"
    stores = build_observability_stores(
        ObservabilitySettings(store_mode="sqlite", sqlite_path=str(db_path))
    )
    context = new_request_context(caller="assistant-api", request_id="req_sqlite")

    stores.audit_store.record(
        request_context=context,
        producer="assistant-api",
        payload={"stage": "response_completed"},
    )
    stores.cost_ledger.record(
        request_context=context,
        producer="assistant-api",
        tenant_id="tenant_123",
        user_id="user_123",
        route="scoped_rag_http",
        usage={"estimatedCostUsd": 0.002, "currency": "USD"},
        metadata={"sessionId": "session_123"},
    )
    stores.feedback_store.record(
        request_context=context,
        producer="assistant-ui",
        tenant_id="tenant_123",
        user_id="user_123",
        session_id="session_123",
        message_id="message_123",
        rating=1,
        categories=["grounded"],
    )

    reopened_repository = SQLiteEventEnvelopeRepository(db_path)
    all_events = reopened_repository.list_events()
    cost_events = reopened_repository.list_events(EventType.COST_EVENT_RECORDED)

    assert [event.event_type for event in all_events] == [
        EventType.AUDIT_RECORD_CREATED,
        EventType.COST_EVENT_RECORDED,
        EventType.FEEDBACK_RECEIVED,
    ]
    assert len(cost_events) == 1
    assert cost_events[0].payload["route"] == "scoped_rag_http"
    assert cost_events[0].payload["metadata"]["sessionId"] == "session_123"


def test_sqlite_repository_clear_removes_persisted_events(tmp_path) -> None:
    db_path = tmp_path / "observability.db"
    stores = build_observability_stores(
        ObservabilitySettings(store_mode="sqlite", sqlite_path=str(db_path))
    )
    context = new_request_context(caller="assistant-api", request_id="req_clear")

    stores.audit_store.record(
        request_context=context,
        producer="assistant-api",
        payload={"stage": "request_received"},
    )
    stores.audit_store.clear()

    reopened_repository = SQLiteEventEnvelopeRepository(db_path)
    assert reopened_repository.list_events() == []
