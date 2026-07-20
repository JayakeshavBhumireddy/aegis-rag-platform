from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from aegis_shared.contracts import (
    Citation,
    EntitlementEnvelope,
    PolicyDecision,
    RequestContext,
    RetrievalResult,
    RetrievalScope,
    RiskLevel,
    UiContext,
    VerificationResult,
)

from assistant_api.settings import AssistantSettings


class DependencyUnavailableError(RuntimeError):
    """Raised when a required downstream service cannot be used safely."""


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    citations: list[Citation]
    confidence: float


class HttpAegisServiceClients:
    def __init__(
        self,
        settings: AssistantSettings,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._client = client or httpx.Client(timeout=settings.request_timeout_seconds)

    def resolve_entitlements(
        self,
        *,
        tenant_id: str,
        user_id: str,
        ui_context: UiContext | None,
    ) -> EntitlementEnvelope:
        response = self._post(
            self._settings.entitlement_url,
            "/v1/entitlements/resolve",
            {
                "tenantId": tenant_id,
                "userId": user_id,
                "uiContext": ui_context.model_dump() if ui_context else None,
            },
        )
        return EntitlementEnvelope.model_validate(response["entitlementEnvelope"])

    def evaluate_policy(
        self,
        *,
        entitlement: EntitlementEnvelope,
        intent: str,
        risk: RiskLevel,
        requested_module: str | None,
        requested_permissions: list[str] | None = None,
    ) -> PolicyDecision:
        response = self._post(
            self._settings.policy_url,
            "/v1/policy/evaluate",
            {
                "entitlementEnvelope": entitlement.model_dump(by_alias=True, mode="json"),
                "intent": intent,
                "risk": risk.value,
                "requestedModule": requested_module,
                "requestedPermissions": requested_permissions or [],
            },
        )
        return PolicyDecision.model_validate(response["policyDecision"])

    def build_context(
        self,
        *,
        session_id: str,
        message: str,
        entitlement: EntitlementEnvelope,
        policy_decision: PolicyDecision,
        ui_context: UiContext | None,
    ) -> dict[str, Any]:
        response = self._post(
            self._settings.context_url,
            "/v1/context/build",
            {
                "sessionId": session_id,
                "message": message,
                "entitlementEnvelope": entitlement.model_dump(by_alias=True, mode="json"),
                "policyDecision": policy_decision.model_dump(by_alias=True, mode="json"),
                "uiContext": ui_context.model_dump() if ui_context else None,
            },
        )
        return dict(response["contextPack"])

    def search(
        self,
        *,
        query: str,
        retrieval_scope: RetrievalScope,
        top_k: int,
    ) -> list[RetrievalResult]:
        response = self._post(
            self._settings.retrieval_url,
            "/v1/retrieval/search",
            {
                "query": query,
                "retrievalScope": retrieval_scope.model_dump(by_alias=True, mode="json"),
                "topK": top_k,
                "retrievalMode": "hybrid",
            },
        )
        return [RetrievalResult.model_validate(result) for result in response["results"]]

    def generate(
        self,
        *,
        message: str,
        retrieval_results: list[RetrievalResult],
    ) -> GenerationResult:
        response = self._post(
            self._settings.llm_gateway_url,
            "/v1/llm/generate",
            {
                "message": message,
                "retrieval_results": [
                    result.model_dump(by_alias=True, mode="json") for result in retrieval_results
                ],
            },
        )
        return GenerationResult(
            answer=response["answer"],
            citations=[Citation.model_validate(citation) for citation in response["citations"]],
            confidence=response["confidence"],
        )

    def verify(
        self,
        *,
        answer: str,
        citations: list[Citation],
        retrieval_results: list[RetrievalResult],
        policy_decision: PolicyDecision,
    ) -> VerificationResult:
        response = self._post(
            self._settings.verification_url,
            "/v1/verification/check",
            {
                "answer": answer,
                "citations": [citation.model_dump(by_alias=True) for citation in citations],
                "retrieval_results": [
                    result.model_dump(by_alias=True, mode="json") for result in retrieval_results
                ],
                "policy_decision": policy_decision.model_dump(by_alias=True, mode="json"),
            },
        )
        return VerificationResult.model_validate(response["verification"])

    def record_audit(
        self,
        *,
        request_context: RequestContext,
        producer: str,
        payload: dict[str, Any],
    ) -> bool:
        return self._post_observability(
            "/v1/audit/records",
            {
                "request_context": request_context.model_dump(by_alias=True, mode="json"),
                "producer": producer,
                "payload": payload,
            },
        )

    def record_cost(
        self,
        *,
        request_context: RequestContext,
        producer: str,
        tenant_id: str,
        user_id: str,
        route: str,
        usage: dict[str, Any],
        metadata: dict[str, Any],
    ) -> bool:
        return self._post_observability(
            "/v1/cost/events",
            {
                "request_context": request_context.model_dump(by_alias=True, mode="json"),
                "producer": producer,
                "tenantId": tenant_id,
                "userId": user_id,
                "route": route,
                "usage": usage,
                "metadata": metadata,
            },
        )

    def _post(self, base_url: str, path: str, json: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(f"{base_url.rstrip('/')}{path}", json=json)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DependencyUnavailableError(f"dependency unavailable: {path}") from exc
        return response.json()

    def _post_observability(self, path: str, json: dict[str, Any]) -> bool:
        try:
            response = self._client.post(
                f"{self._settings.observability_url.rstrip('/')}{path}",
                json=json,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        return True
