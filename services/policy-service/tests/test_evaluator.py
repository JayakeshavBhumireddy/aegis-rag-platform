from __future__ import annotations

from aegis_shared.contracts import PolicyDecisionValue, RiskLevel
from entitlement_service.resolver import InMemoryEntitlementStore, resolve_entitlement_envelope
from policy_service.evaluator import (
    evaluate_policy,
    infer_intent,
    infer_requested_module,
    infer_requested_permissions,
)


def test_allows_licensed_module_scope() -> None:
    entitlement = resolve_entitlement_envelope("tenant_123", "user_123", InMemoryEntitlementStore())

    decision = evaluate_policy(
        entitlement=entitlement,
        intent="navigation",
        risk=RiskLevel.LOW,
        requested_module="Billing",
    )

    assert decision.decision == PolicyDecisionValue.ALLOW
    assert decision.retrieval_scope is not None
    assert decision.retrieval_scope.modules == ["Billing"]


def test_denies_unlicensed_module() -> None:
    entitlement = resolve_entitlement_envelope("tenant_123", "user_123", InMemoryEntitlementStore())

    decision = evaluate_policy(
        entitlement=entitlement,
        intent="workflow_help",
        risk=RiskLevel.LOW,
        requested_module="Inventory",
    )

    assert decision.decision == PolicyDecisionValue.DENY
    assert decision.can_answer is False


def test_denies_missing_action_permission() -> None:
    entitlement = resolve_entitlement_envelope("tenant_123", "user_123", InMemoryEntitlementStore())

    decision = evaluate_policy(
        entitlement=entitlement,
        intent="workflow_help",
        risk=RiskLevel.LOW,
        requested_module="Billing",
        requested_permissions=["Billing.Admin"],
    )

    assert decision.decision == PolicyDecisionValue.DENY
    assert decision.can_retrieve is False
    assert "Billing.Admin" in decision.reasons[0]


def test_infers_intent_and_module() -> None:
    assert infer_intent("Where do I submit monthly billing?") == "navigation"
    assert infer_requested_module("How do I receive inventory?") == "Inventory"
    assert infer_requested_permissions("Can I submit monthly billing?", "Billing") == [
        "Billing.Submit"
    ]
