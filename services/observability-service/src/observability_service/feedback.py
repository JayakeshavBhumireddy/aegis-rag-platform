from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aegis_shared.contracts import EventEnvelope, EventType, RequestContext

from observability_service.event_repository import SQLiteEventEnvelopeRepository


class InMemoryFeedbackStore:
    def __init__(self) -> None:
        self._events: list[EventEnvelope] = []

    def record(
        self,
        *,
        request_context: RequestContext,
        producer: str,
        tenant_id: str,
        user_id: str,
        session_id: str,
        message_id: str,
        rating: int,
        comment: str | None = None,
        categories: list[str] | None = None,
        metadata: dict | None = None,
    ) -> EventEnvelope:
        event = EventEnvelope(
            eventId=f"evt_{uuid4().hex}",
            eventType=EventType.FEEDBACK_RECEIVED,
            eventVersion="v1",
            occurredAt=datetime.now(UTC),
            requestId=request_context.request_id,
            traceId=request_context.trace_id,
            producer=producer,
            payload={
                "tenantId": tenant_id,
                "userId": user_id,
                "sessionId": session_id,
                "messageId": message_id,
                "rating": rating,
                "comment": comment,
                "categories": categories or [],
                "metadata": metadata or {},
            },
        )
        self._events.append(event)
        return event

    def list_events(self) -> list[EventEnvelope]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()


class SQLiteFeedbackStore:
    def __init__(self, repository: SQLiteEventEnvelopeRepository) -> None:
        self._repository = repository

    def record(
        self,
        *,
        request_context: RequestContext,
        producer: str,
        tenant_id: str,
        user_id: str,
        session_id: str,
        message_id: str,
        rating: int,
        comment: str | None = None,
        categories: list[str] | None = None,
        metadata: dict | None = None,
    ) -> EventEnvelope:
        return self._repository.record(
            EventEnvelope(
                eventId=f"evt_{uuid4().hex}",
                eventType=EventType.FEEDBACK_RECEIVED,
                eventVersion="v1",
                occurredAt=datetime.now(UTC),
                requestId=request_context.request_id,
                traceId=request_context.trace_id,
                producer=producer,
                payload={
                    "tenantId": tenant_id,
                    "userId": user_id,
                    "sessionId": session_id,
                    "messageId": message_id,
                    "rating": rating,
                    "comment": comment,
                    "categories": categories or [],
                    "metadata": metadata or {},
                },
            )
        )

    def list_events(self) -> list[EventEnvelope]:
        return self._repository.list_events(EventType.FEEDBACK_RECEIVED)

    def clear(self) -> None:
        self._repository.clear()


GLOBAL_FEEDBACK_STORE = InMemoryFeedbackStore()
