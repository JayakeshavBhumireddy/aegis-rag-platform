from __future__ import annotations

import pytest
from aegis_shared.contracts import DataAccessMode
from entitlement_service.resolver import (
    EntitlementResolutionError,
    InMemoryEntitlementStore,
    PrincipalEntitlements,
    resolve_entitlement_envelope,
    stable_scope_hash,
)


def test_resolves_entitlement_envelope_for_known_principal() -> None:
    store = InMemoryEntitlementStore()

    envelope = resolve_entitlement_envelope(
        tenant_id="tenant_123",
        user_id="user_123",
        store=store,
    )

    assert envelope.tenant_id == "tenant_123"
    assert envelope.user_id == "user_123"
    assert envelope.licensed_modules == ["Billing", "Reports"]
    assert envelope.permissions == ["Billing.View", "Billing.Submit"]
    assert envelope.license_hash == stable_scope_hash(("Billing", "Reports"))
    assert envelope.permission_hash == stable_scope_hash(("Billing.View", "Billing.Submit"))


def test_fails_closed_for_unknown_principal() -> None:
    store = InMemoryEntitlementStore()

    with pytest.raises(EntitlementResolutionError):
        resolve_entitlement_envelope(
            tenant_id="tenant_missing",
            user_id="user_missing",
            store=store,
        )


def test_fails_closed_for_disabled_principal() -> None:
    store = InMemoryEntitlementStore(
        principals=[
            PrincipalEntitlements(
                tenant_id="tenant_disabled",
                user_id="user_disabled",
                region="us",
                product_version="2026.2",
                licensed_modules=("Billing",),
                enabled_features=(),
                role="Viewer",
                permissions=("Billing.View",),
                data_access_mode=DataAccessMode.DISABLED,
            )
        ]
    )

    with pytest.raises(EntitlementResolutionError):
        resolve_entitlement_envelope(
            tenant_id="tenant_disabled",
            user_id="user_disabled",
            store=store,
        )
