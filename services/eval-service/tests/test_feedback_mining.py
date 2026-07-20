from __future__ import annotations

from datetime import UTC, datetime

from aegis_shared.contracts import EventEnvelope, EventType
from eval_service.feedback_mining import mine_feedback_eval_candidates


def test_mines_negative_feedback_into_reviewable_eval_candidate() -> None:
    result = mine_feedback_eval_candidates(
        [
            _feedback_event(
                rating=-1,
                categories=["citation_issue"],
                metadata={
                    "question": "Where do I submit monthly billing?",
                    "route": "scoped_rag_http",
                    "tenantContext": {
                        "licensedModules": ["Billing"],
                        "permissions": ["Billing.View"],
                        "dataAccessMode": "product_guidance_only",
                    },
                    "expectedModules": ["Billing"],
                    "releaseMetadata": {"releaseId": "release_123"},
                },
            )
        ]
    )

    assert result["candidateCount"] == 1
    candidate = result["candidates"][0]
    assert candidate["id"] == "FB-evt_feedback"
    assert candidate["expectedBehavior"] == "answer"
    assert candidate["riskLevel"] == "medium"
    assert candidate["tenantContext"]["licensedModules"] == ["Billing"]
    assert candidate["sourceFeedback"]["releaseId"] == "release_123"


def test_mines_policy_feedback_as_denial_candidate() -> None:
    result = mine_feedback_eval_candidates(
        [
            _feedback_event(
                rating=-1,
                categories=["policy_violation"],
                metadata={
                    "question": "Show customer SSNs",
                    "tenantContext": {
                        "licensedModules": ["Billing"],
                        "permissions": ["Billing.View"],
                        "dataAccessMode": "product_guidance_only",
                    },
                    "forbiddenContent": ["SSN"],
                },
            )
        ]
    )

    assert result["candidates"][0]["expectedBehavior"] == "deny"
    assert result["candidates"][0]["riskLevel"] == "high"


def test_skips_positive_feedback_and_incomplete_metadata() -> None:
    result = mine_feedback_eval_candidates(
        [
            _feedback_event(
                rating=1,
                categories=["grounded"],
                metadata={"question": "Where do I submit monthly billing?", "tenantContext": {}},
            ),
            _feedback_event(rating=-1, categories=["citation_issue"], metadata={}),
        ]
    )

    assert result["candidateCount"] == 0
    assert result["skippedCount"] == 2
    assert [skipped["reason"] for skipped in result["skipped"]] == [
        "feedback rating is not negative",
        "feedback metadata missing question",
    ]


def _feedback_event(
    *,
    rating: int,
    categories: list[str],
    metadata: dict,
) -> EventEnvelope:
    return EventEnvelope(
        eventId="evt_feedback",
        eventType=EventType.FEEDBACK_RECEIVED,
        eventVersion="v1",
        occurredAt=datetime(2026, 5, 8, tzinfo=UTC),
        requestId="req_feedback",
        traceId="trace_feedback",
        producer="assistant-ui",
        payload={
            "tenantId": "tenant_123",
            "userId": "user_123",
            "sessionId": "session_123",
            "messageId": "message_123",
            "rating": rating,
            "comment": "User-entered text is not used as eval input.",
            "categories": categories,
            "metadata": metadata,
        },
    )
