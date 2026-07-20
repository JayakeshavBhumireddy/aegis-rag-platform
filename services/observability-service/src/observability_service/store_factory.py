from __future__ import annotations

from dataclasses import dataclass

from observability_service.audit import GLOBAL_AUDIT_STORE, SQLiteAuditStore
from observability_service.costs import GLOBAL_COST_LEDGER, SQLiteCostLedger
from observability_service.event_repository import SQLiteEventEnvelopeRepository
from observability_service.feedback import GLOBAL_FEEDBACK_STORE, SQLiteFeedbackStore
from observability_service.settings import ObservabilitySettings


@dataclass(frozen=True)
class ObservabilityStores:
    audit_store: object
    cost_ledger: object
    feedback_store: object


def build_observability_stores(settings: ObservabilitySettings) -> ObservabilityStores:
    if settings.store_mode == "memory":
        return ObservabilityStores(
            audit_store=GLOBAL_AUDIT_STORE,
            cost_ledger=GLOBAL_COST_LEDGER,
            feedback_store=GLOBAL_FEEDBACK_STORE,
        )
    if settings.store_mode == "sqlite":
        repository = SQLiteEventEnvelopeRepository(settings.resolved_sqlite_path())
        return ObservabilityStores(
            audit_store=SQLiteAuditStore(repository),
            cost_ledger=SQLiteCostLedger(repository),
            feedback_store=SQLiteFeedbackStore(repository),
        )
    raise ValueError(f"unsupported observability store mode: {settings.store_mode}")
