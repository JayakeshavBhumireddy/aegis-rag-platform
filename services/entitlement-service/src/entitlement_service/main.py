from __future__ import annotations

import sqlite3
from typing import Annotated

from aegis_shared.contracts import EntitlementEnvelope, UiContext
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from entitlement_service.metadata_repository import MetadataEntitlementRepository
from entitlement_service.resolver import (
    EntitlementResolutionError,
    EntitlementStore,
    InMemoryEntitlementStore,
    resolve_entitlement_envelope,
)
from entitlement_service.settings import EntitlementSettings

SERVICE_VERSION = "entitlement-service-v0"

app = FastAPI(title="AegisRAG entitlement-service", version=SERVICE_VERSION)
store = InMemoryEntitlementStore()


class EntitlementResolveRequest(BaseModel):
    tenant_id: str = Field(alias="tenantId", min_length=1)
    user_id: str = Field(alias="userId", min_length=1)
    ui_context: UiContext | None = Field(alias="uiContext", default=None)


class EntitlementResolveResponse(BaseModel):
    entitlement_envelope: EntitlementEnvelope = Field(alias="entitlementEnvelope")


def get_store() -> EntitlementStore:
    settings = EntitlementSettings.from_env()
    if settings.store_mode == "metadata":
        if not settings.sqlite_path:
            raise EntitlementResolutionError("metadata store requires sqlite path")
        connection = sqlite3.connect(settings.sqlite_path)
        connection.row_factory = sqlite3.Row
        return MetadataEntitlementRepository(connection)
    return store


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/entitlements/resolve", response_model=EntitlementResolveResponse)
def resolve_entitlements(
    request: EntitlementResolveRequest,
    entitlement_store: Annotated[EntitlementStore, Depends(get_store)],
) -> EntitlementResolveResponse:
    try:
        envelope = resolve_entitlement_envelope(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            store=entitlement_store,
        )
    except EntitlementResolutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ENTITLEMENT_UNAVAILABLE",
                "message": "Entitlement envelope could not be resolved.",
            },
        ) from exc

    return EntitlementResolveResponse(entitlementEnvelope=envelope)
