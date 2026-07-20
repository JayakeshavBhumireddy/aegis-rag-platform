from __future__ import annotations

from aegis_shared.contracts import (
    DataAccessMode,
    EntitlementEnvelope,
    PolicyDecision,
    PolicyDecisionValue,
    RetrievalScope,
    RiskLevel,
)

CUSTOMER_DATA_INTENTS = {"customer_data_request", "financial_record_request", "person_lookup"}


def infer_requested_module(message: str, fallback_module: str | None = None) -> str | None:
    normalized = message.lower()
    if "billing" in normalized or "invoice" in normalized or "monthly" in normalized:
        return "Billing"
    if "inventory" in normalized or "receiv" in normalized or "stock" in normalized:
        return "Inventory"
    return fallback_module


def infer_intent(message: str) -> str:
    normalized = message.lower()
    if any(term in normalized for term in ("customer", "ssn", "credit card", "bank account")):
        return "customer_data_request"
    injection_terms = ("ignore previous", "system prompt", "developer message")
    if any(term in normalized for term in injection_terms):
        return "unsafe_or_injection"
    if any(term in normalized for term in ("where", "open", "go to", "navigate")):
        return "navigation"
    return "workflow_help"


def infer_requested_permissions(message: str, requested_module: str | None) -> list[str]:
    if not requested_module:
        return []
    normalized = message.lower()
    permissions: list[str] = []
    if "submit" in normalized:
        permissions.append(f"{requested_module}.Submit")
    if "receive" in normalized or "receiving" in normalized:
        permissions.append(f"{requested_module}.Receive")
    if any(term in normalized for term in ("where", "open", "go to", "navigate", "view")):
        permissions.append(f"{requested_module}.View")
    return sorted(set(permissions))


def evaluate_policy(
    *,
    entitlement: EntitlementEnvelope,
    intent: str,
    risk: RiskLevel,
    requested_module: str | None,
    requested_permissions: list[str] | None = None,
) -> PolicyDecision:
    reasons: list[str] = []

    if intent == "unsafe_or_injection":
        return _deny(["prompt injection or unsafe instruction detected"])

    if (
        intent in CUSTOMER_DATA_INTENTS
        and entitlement.data_access_mode != DataAccessMode.SECURE_CUSTOMER_DATA
    ):
        return _deny(["customer data access is disabled for this entitlement"])

    if risk == RiskLevel.HIGH:
        return PolicyDecision(
            decision=PolicyDecisionValue.ESCALATE,
            canRetrieve=False,
            canAnswer=False,
            canCache=False,
            mustEscalate=True,
            retrievalScope=None,
            reasons=["high risk request requires escalation"],
        )

    modules = entitlement.licensed_modules
    if requested_module and requested_module not in modules:
        reasons.append(f"module not licensed: {requested_module}")

    if not entitlement.permissions:
        reasons.append("no permissions available")

    missing_permissions = sorted(set(requested_permissions or []) - set(entitlement.permissions))
    if missing_permissions:
        reasons.append(f"permissions not granted: {', '.join(missing_permissions)}")

    if reasons:
        return _deny(reasons)

    return PolicyDecision(
        decision=PolicyDecisionValue.ALLOW,
        canRetrieve=True,
        canAnswer=True,
        canCache=True,
        mustEscalate=False,
        retrievalScope=RetrievalScope(
            tenantId=entitlement.tenant_id,
            modules=[requested_module] if requested_module else modules,
            permissions=entitlement.permissions,
            productVersion=entitlement.product_version,
            trustLevel="approved",
            region=entitlement.region,
        ),
        reasons=[],
    )


def _deny(reasons: list[str]) -> PolicyDecision:
    return PolicyDecision(
        decision=PolicyDecisionValue.DENY,
        canRetrieve=False,
        canAnswer=False,
        canCache=False,
        mustEscalate=False,
        retrievalScope=None,
        reasons=reasons,
    )
