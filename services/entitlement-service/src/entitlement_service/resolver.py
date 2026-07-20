from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from aegis_shared.contracts import DataAccessMode, EntitlementEnvelope


class EntitlementResolutionError(RuntimeError):
    """Raised when an entitlement envelope cannot be resolved safely."""


@dataclass(frozen=True)
class PrincipalEntitlements:
    tenant_id: str
    user_id: str
    region: str
    product_version: str
    licensed_modules: tuple[str, ...]
    enabled_features: tuple[str, ...]
    role: str
    permissions: tuple[str, ...]
    data_access_mode: DataAccessMode


class InMemoryEntitlementStore:
    def __init__(self, principals: list[PrincipalEntitlements] | None = None) -> None:
        self._principals = {
            (principal.tenant_id, principal.user_id): principal
            for principal in (principals or default_principals())
        }

    def get(self, tenant_id: str, user_id: str) -> PrincipalEntitlements | None:
        return self._principals.get((tenant_id, user_id))


class EntitlementStore(Protocol):
    def get(self, tenant_id: str, user_id: str) -> PrincipalEntitlements | None: ...


def stable_scope_hash(values: tuple[str, ...]) -> str:
    canonical = "\n".join(sorted(values))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def resolve_entitlement_envelope(
    tenant_id: str,
    user_id: str,
    store: EntitlementStore,
) -> EntitlementEnvelope:
    principal = store.get(tenant_id=tenant_id, user_id=user_id)
    if principal is None:
        raise EntitlementResolutionError("entitlement principal not found")
    if principal.data_access_mode == DataAccessMode.DISABLED:
        raise EntitlementResolutionError("entitlement principal is disabled")
    if not principal.licensed_modules or not principal.permissions:
        raise EntitlementResolutionError("entitlement principal has incomplete scope")

    return EntitlementEnvelope(
        tenantId=principal.tenant_id,
        userId=principal.user_id,
        region=principal.region,
        productVersion=principal.product_version,
        licensedModules=list(principal.licensed_modules),
        enabledFeatures=list(principal.enabled_features),
        role=principal.role,
        permissions=list(principal.permissions),
        licenseHash=stable_scope_hash(principal.licensed_modules),
        permissionHash=stable_scope_hash(principal.permissions),
        dataAccessMode=principal.data_access_mode,
    )


def default_principals() -> list[PrincipalEntitlements]:
    return [
        PrincipalEntitlements(
            tenant_id="tenant_123",
            user_id="user_123",
            region="us",
            product_version="2026.2",
            licensed_modules=("Billing", "Reports"),
            enabled_features=("MonthlySubmission",),
            role="TenantAdmin",
            permissions=("Billing.View", "Billing.Submit"),
            data_access_mode=DataAccessMode.PRODUCT_GUIDANCE_ONLY,
        )
    ]
