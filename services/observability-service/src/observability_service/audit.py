from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aegis_shared.contracts import EventEnvelope, EventType, RequestContext

from observability_service.event_repository import SQLiteEventEnvelopeRepository


class InMemoryAuditStore:
    def __init__(self) -> None:
        self._events: list[EventEnvelope] = []

    def record(
        self,
        *,
        request_context: RequestContext,
        producer: str,
        payload: dict,
    ) -> EventEnvelope:
        event = EventEnvelope(
            eventId=f"evt_{uuid4().hex}",
            eventType=EventType.AUDIT_RECORD_CREATED,
            eventVersion="v1",
            occurredAt=datetime.now(UTC),
            requestId=request_context.request_id,
            traceId=request_context.trace_id,
            producer=producer,
            payload=payload,
        )
        self._events.append(event)
        return event

    def list_events(self) -> list[EventEnvelope]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()


class SQLiteAuditStore:
    def __init__(self, repository: SQLiteEventEnvelopeRepository) -> None:
        self._repository = repository

    def record(
        self,
        *,
        request_context: RequestContext,
        producer: str,
        payload: dict,
    ) -> EventEnvelope:
        return self._repository.record(
            EventEnvelope(
                eventId=f"evt_{uuid4().hex}",
                eventType=EventType.AUDIT_RECORD_CREATED,
                eventVersion="v1",
                occurredAt=datetime.now(UTC),
                requestId=request_context.request_id,
                traceId=request_context.trace_id,
                producer=producer,
                payload=payload,
            )
        )

    def list_events(self) -> list[EventEnvelope]:
        return self._repository.list_events(EventType.AUDIT_RECORD_CREATED)

    def clear(self) -> None:
        self._repository.clear()


GLOBAL_AUDIT_STORE = InMemoryAuditStore()
