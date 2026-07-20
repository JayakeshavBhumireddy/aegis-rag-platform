from __future__ import annotations

from aegis_shared.contracts import ChatRequest, UiContext
from aegis_shared.runtime import new_request_context
from assistant_api.cache import ExactAnswerCache
from assistant_api.orchestrator import answer_message
from assistant_api.release_state import ActiveRelease
from observability_service.audit import InMemoryAuditStore
from observability_service.costs import InMemoryCostLedger


def test_answers_allowed_billing_navigation() -> None:
    response = answer_message(
        ChatRequest(
            message="Where do I submit monthly billing?",
            tenantId="tenant_123",
            userId="user_123",
            sessionId="session_123",
            uiContext=UiContext(module="Billing", page="Monthly Submission"),
        ),
        exact_cache=ExactAnswerCache(),
    )

    assert response.route == "navigation_graph"
    assert "Billing > Monthly Submission" in response.answer
    assert response.citations
    assert response.usage["estimatedCostUsd"] <= 0.001
    assert response.usage["estimatedLatencyMs"] <= 800


def test_reuses_entitlement_scoped_exact_cache() -> None:
    cache = ExactAnswerCache()
    request = ChatRequest(
        message="Where do I submit monthly billing?",
        tenantId="tenant_123",
        userId="user_123",
        sessionId="session_123",
        uiContext=UiContext(module="Billing", page="Monthly Submission"),
    )

    first_response = answer_message(request, exact_cache=cache)
    second_response = answer_message(request, exact_cache=cache)

    assert first_response.route == "navigation_graph"
    assert second_response.route == "exact_cache"
    assert second_response.answer == first_response.answer
    assert second_response.usage["estimatedCostUsd"] == 0.0


def test_denies_unlicensed_inventory_navigation() -> None:
    response = answer_message(
        ChatRequest(
            message="How do I receive inventory?",
            tenantId="tenant_123",
            userId="user_123",
            sessionId="session_123",
            uiContext=UiContext(module="Inventory"),
        ),
        exact_cache=ExactAnswerCache(),
    )

    assert response.route == "denial_or_escalation"
    assert response.citations == []
    assert response.usage["estimatedCostUsd"] == 0.0


def test_records_audit_events_for_answer_flow() -> None:
    audit_store = InMemoryAuditStore()
    cost_ledger = InMemoryCostLedger()
    request_context = new_request_context(caller="assistant-api", request_id="req_test")

    response = answer_message(
        ChatRequest(
            message="Where do I submit monthly billing?",
            tenantId="tenant_123",
            userId="user_123",
            sessionId="session_123",
            uiContext=UiContext(module="Billing", page="Monthly Submission"),
        ),
        exact_cache=ExactAnswerCache(),
        audit_store=audit_store,
        cost_ledger=cost_ledger,
        request_context=request_context,
        active_release=_active_release("release_test"),
    )

    stages = [event.payload["stage"] for event in audit_store.list_events()]
    assert response.route == "navigation_graph"
    assert stages == [
        "request_received",
        "entitlement_resolved",
        "policy_evaluated",
        "verification_completed",
        "response_completed",
    ]
    assert {event.request_id for event in audit_store.list_events()} == {"req_test"}
    completed = audit_store.list_events()[-1]
    assert completed.payload["usage"]["estimatedCostUsd"] <= 0.001
    assert response.release_metadata["releaseId"] == "release_test"
    assert audit_store.list_events()[0].payload["releaseMetadata"]["releaseId"] == "release_test"
    cost_events = cost_ledger.list_events()
    assert len(cost_events) == 1
    assert cost_events[0].request_id == "req_test"
    assert cost_events[0].payload["tenantId"] == "tenant_123"
    assert cost_events[0].payload["route"] == response.route
    assert cost_events[0].payload["usage"] == response.usage
    assert cost_events[0].payload["metadata"]["releaseMetadata"]["releaseId"] == "release_test"


def test_exact_cache_is_scoped_to_active_release() -> None:
    cache = ExactAnswerCache()
    request = ChatRequest(
        message="Where do I submit monthly billing?",
        tenantId="tenant_123",
        userId="user_123",
        sessionId="session_123",
        uiContext=UiContext(module="Billing", page="Monthly Submission"),
    )

    first_response = answer_message(
        request,
        exact_cache=cache,
        active_release=_active_release("release_one"),
    )
    second_response = answer_message(
        request,
        exact_cache=cache,
        active_release=_active_release("release_two"),
    )
    third_response = answer_message(
        request,
        exact_cache=cache,
        active_release=_active_release("release_one"),
    )

    assert first_response.route == "navigation_graph"
    assert second_response.route == "navigation_graph"
    assert second_response.release_metadata["releaseId"] == "release_two"
    assert third_response.route == "exact_cache"
    assert third_response.release_metadata["releaseId"] == "release_one"


def _active_release(release_id: str) -> ActiveRelease:
    return ActiveRelease(
        metadata={
            "releaseId": release_id,
            "status": "prod",
            "appVersion": "0.1.0",
            "contentVersion": "content-v1",
            "indexVersion": "index-v1",
            "promptVersion": "answer-prompt-v1",
            "policyVersion": "policy-baseline-v1",
            "guardrailVersion": "guardrails-local-v1",
            "routerConfigVersion": "inference-routes-v1",
        }
    )
