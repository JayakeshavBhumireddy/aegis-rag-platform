from __future__ import annotations

import re
from dataclasses import dataclass, field

from aegis_shared.contracts import ChatResponse, EntitlementEnvelope, RetrievalScope

from assistant_api.costing import estimate_usage


def normalize_cache_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def entitlement_cache_scope(entitlement: EntitlementEnvelope, scope: RetrievalScope) -> str:
    modules = ",".join(sorted(scope.modules))
    return ":".join(
        [
            entitlement.tenant_id,
            entitlement.user_id,
            entitlement.product_version,
            entitlement.license_hash,
            entitlement.permission_hash,
            modules,
            scope.trust_level,
        ]
    )


@dataclass
class ExactAnswerCache:
    _responses: dict[str, ChatResponse] = field(default_factory=dict)

    def get(
        self,
        *,
        message: str,
        entitlement: EntitlementEnvelope,
        scope: RetrievalScope,
        release_id: str = "local-unpromoted",
    ) -> ChatResponse | None:
        return self._responses.get(self._key(message, entitlement, scope, release_id))

    def set(
        self,
        *,
        message: str,
        entitlement: EntitlementEnvelope,
        scope: RetrievalScope,
        response: ChatResponse,
        release_id: str = "local-unpromoted",
    ) -> None:
        if response.route in {"denial_or_escalation", "verification_failed", "retrieval_empty"}:
            return
        self._responses[self._key(message, entitlement, scope, release_id)] = response.model_copy(
            update={
                "route": "exact_cache",
                "usage": estimate_usage(
                    "exact_cache",
                    input_text=message,
                    output_text=response.answer,
                ),
            }
        )

    def clear(self) -> None:
        self._responses.clear()

    @staticmethod
    def _key(
        message: str,
        entitlement: EntitlementEnvelope,
        scope: RetrievalScope,
        release_id: str,
    ) -> str:
        return (
            f"{release_id}:{entitlement_cache_scope(entitlement, scope)}:"
            f"{normalize_cache_text(message)}"
        )


GLOBAL_EXACT_CACHE = ExactAnswerCache()
