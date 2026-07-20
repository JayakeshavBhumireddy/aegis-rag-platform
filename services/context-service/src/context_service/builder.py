from __future__ import annotations

from typing import Any

from aegis_shared.contracts import EntitlementEnvelope, PolicyDecision, UiContext


def build_context_pack(
    *,
    session_id: str,
    message: str,
    entitlement: EntitlementEnvelope,
    policy_decision: PolicyDecision,
    ui_context: UiContext | None,
) -> dict[str, Any]:
    return {
        "sessionId": session_id,
        "recentTurns": [],
        "sessionSummary": None,
        "safeUserMemory": [],
        "tenantContext": {
            "tenantId": entitlement.tenant_id,
            "region": entitlement.region,
            "productVersion": entitlement.product_version,
            "licensedModules": entitlement.licensed_modules,
        },
        "uiContext": ui_context.model_dump() if ui_context else {},
        "policy": policy_decision.model_dump(by_alias=True),
        "redactions": [],
        "messagePreview": message[:200],
    }
