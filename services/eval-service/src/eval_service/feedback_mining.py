from __future__ import annotations

from typing import Any

from aegis_shared.contracts import (
    EventEnvelope,
    EventType,
    ExpectedBehavior,
    RiskLevel,
)


def mine_feedback_eval_candidates(events: list[EventEnvelope]) -> dict[str, Any]:
    candidates = []
    skipped = []
    for event in events:
        candidate, reason = _candidate_from_event(event)
        if candidate is None:
            skipped.append({"eventId": event.event_id, "reason": reason})
        else:
            candidates.append(candidate)
    return {
        "totalFeedbackEvents": len(events),
        "candidateCount": len(candidates),
        "skippedCount": len(skipped),
        "candidates": candidates,
        "skipped": skipped,
    }


def _candidate_from_event(event: EventEnvelope) -> tuple[dict[str, Any] | None, str]:
    if event.event_type != EventType.FEEDBACK_RECEIVED:
        return None, "not a feedback event"
    payload = event.payload
    if int(payload.get("rating", 0)) >= 0:
        return None, "feedback rating is not negative"

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        return None, "feedback metadata is not an object"
    question = metadata.get("question")
    if not isinstance(question, str) or not question.strip():
        return None, "feedback metadata missing question"
    tenant_context = metadata.get("tenantContext")
    if not isinstance(tenant_context, dict):
        return None, "feedback metadata missing tenantContext"

    categories = payload.get("categories", [])
    if not isinstance(categories, list):
        categories = []
    expected_behavior = _expected_behavior(categories)
    risk_level = (
        RiskLevel.HIGH if expected_behavior != ExpectedBehavior.ANSWER else RiskLevel.MEDIUM
    )

    return (
        {
            "id": f"FB-{event.event_id}",
            "question": question,
            "tenantContext": tenant_context,
            "expectedBehavior": expected_behavior.value,
            "expectedModules": list(metadata.get("expectedModules", [])),
            "forbiddenContent": list(metadata.get("forbiddenContent", [])),
            "mustCiteSource": bool(metadata.get("mustCiteSource", True)),
            "riskLevel": risk_level.value,
            "sourceFeedback": {
                "eventId": event.event_id,
                "requestId": event.request_id,
                "traceId": event.trace_id,
                "categories": categories,
                "route": metadata.get("route"),
                "releaseId": metadata.get("releaseMetadata", {}).get("releaseId")
                if isinstance(metadata.get("releaseMetadata"), dict)
                else None,
            },
        },
        "",
    )


def _expected_behavior(categories: list[Any]) -> ExpectedBehavior:
    normalized = {str(category).lower() for category in categories}
    if normalized & {"unsafe_answer", "policy_violation", "permission_issue", "pii_issue"}:
        return ExpectedBehavior.DENY
    if normalized & {"needs_escalation", "unsupported"}:
        return ExpectedBehavior.ESCALATE
    return ExpectedBehavior.ANSWER
