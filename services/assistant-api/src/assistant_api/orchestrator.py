from __future__ import annotations

from aegis_shared.contracts import (
    AuthenticatedPrincipal,
    ChatRequest,
    ChatResponse,
    PolicyDecision,
    PolicyDecisionValue,
    RequestContext,
    RetrievalResult,
    RiskLevel,
)
from aegis_shared.runtime import new_request_context
from context_service.builder import build_context_pack
from entitlement_service.resolver import InMemoryEntitlementStore, resolve_entitlement_envelope
from llm_gateway.generator import generate_answer
from observability_service.audit import GLOBAL_AUDIT_STORE, InMemoryAuditStore
from observability_service.costs import GLOBAL_COST_LEDGER, InMemoryCostLedger
from policy_service.evaluator import (
    evaluate_policy,
    infer_intent,
    infer_requested_module,
    infer_requested_permissions,
)
from retrieval_service.search import search_corpus
from verification_service.verifier import verify_answer

from assistant_api.cache import GLOBAL_EXACT_CACHE, ExactAnswerCache
from assistant_api.costing import estimate_usage
from assistant_api.navigation import find_navigation_route
from assistant_api.release_state import ActiveRelease, load_active_release
from assistant_api.service_clients import HttpAegisServiceClients


def answer_message(
    request: ChatRequest,
    *,
    principal: AuthenticatedPrincipal | None = None,
    entitlement_store: InMemoryEntitlementStore | None = None,
    exact_cache: ExactAnswerCache | None = None,
    audit_store: InMemoryAuditStore | None = None,
    cost_ledger: InMemoryCostLedger | None = None,
    request_context: RequestContext | None = None,
    active_release: ActiveRelease | None = None,
) -> ChatResponse:
    store = entitlement_store or InMemoryEntitlementStore()
    cache = exact_cache or GLOBAL_EXACT_CACHE
    audit = audit_store or GLOBAL_AUDIT_STORE
    costs = cost_ledger or GLOBAL_COST_LEDGER
    context = request_context or new_request_context(caller="assistant-api")
    release = active_release or load_active_release()
    _record_audit(
        audit,
        context,
        stage="request_received",
        payload={
            "tenantId": request.tenant_id,
            "userId": request.user_id,
            "subject": principal.subject if principal else None,
            "releaseMetadata": release.metadata,
        },
    )
    entitlement = resolve_entitlement_envelope(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        store=store,
    )
    _record_audit(
        audit,
        context,
        stage="entitlement_resolved",
        payload={
            "licenseHash": entitlement.license_hash,
            "permissionHash": entitlement.permission_hash,
            "dataAccessMode": entitlement.data_access_mode,
        },
    )

    requested_module = infer_requested_module(
        request.message,
        fallback_module=request.ui_context.module if request.ui_context else None,
    )
    intent = infer_intent(request.message)
    requested_permissions = infer_requested_permissions(request.message, requested_module)
    policy = evaluate_policy(
        entitlement=entitlement,
        intent=intent,
        risk=RiskLevel.LOW,
        requested_module=requested_module,
        requested_permissions=requested_permissions,
    )
    _record_audit(
        audit,
        context,
        stage="policy_evaluated",
        payload={
            "decision": policy.decision,
            "intent": intent,
            "requestedModule": requested_module,
            "requestedPermissions": requested_permissions,
            "reasons": policy.reasons,
        },
    )

    if policy.decision != PolicyDecisionValue.ALLOW or policy.retrieval_scope is None:
        response = ChatResponse(
            answer="I cannot answer that with your current access.",
            citations=[],
            confidence=0.0,
            route="denial_or_escalation",
            escalation={"reasons": policy.reasons} if policy.must_escalate else None,
        )
        response = _with_usage(response, input_text=request.message, active_release=release)
        _record_audit(
            audit,
            context,
            stage="response_denied",
            payload={"route": response.route, "usage": response.usage},
        )
        _record_cost(costs, context, request=request, response=response)
        return response

    build_context_pack(
        session_id=request.session_id,
        message=request.message,
        entitlement=entitlement,
        policy_decision=policy,
        ui_context=request.ui_context,
    )

    cached_response = cache.get(
        message=request.message,
        entitlement=entitlement,
        scope=policy.retrieval_scope,
        release_id=release.release_id,
    )
    if cached_response is not None:
        _record_audit(
            audit,
            context,
            stage="cache_hit",
            payload={"route": cached_response.route, "usage": cached_response.usage},
        )
        _record_cost(costs, context, request=request, response=cached_response)
        return cached_response

    navigation_result = find_navigation_route(
        query=request.message,
        retrieval_scope=policy.retrieval_scope,
    )
    if navigation_result is not None:
        response = _generate_verified_response(
            request=request,
            retrieval_results=[navigation_result],
            route="navigation_graph",
            policy=policy,
            audit_store=audit,
            request_context=context,
            active_release=release,
        )
        if policy.can_cache:
            cache.set(
                message=request.message,
                entitlement=entitlement,
                scope=policy.retrieval_scope,
                response=response,
                release_id=release.release_id,
            )
        _record_audit(
            audit,
            context,
            stage="response_completed",
            payload={
                "route": response.route,
                "citationCount": len(response.citations),
                "usage": response.usage,
            },
        )
        _record_cost(costs, context, request=request, response=response)
        return response

    retrieval_results = search_corpus(
        query=request.message,
        retrieval_scope=policy.retrieval_scope,
        top_k=5,
    )
    if not retrieval_results:
        response = ChatResponse(
            answer="I could not find approved context that matches your request.",
            citations=[],
            confidence=0.0,
            route="retrieval_empty",
            escalation=None,
        )
        response = _with_usage(response, input_text=request.message, active_release=release)
        _record_audit(
            audit,
            context,
            stage="retrieval_empty",
            payload={"route": response.route, "usage": response.usage},
        )
        _record_cost(costs, context, request=request, response=response)
        return response
    _record_audit(
        audit,
        context,
        stage="retrieval_completed",
        payload={"resultCount": len(retrieval_results)},
    )

    response = _generate_verified_response(
        request=request,
        retrieval_results=retrieval_results,
        route="scoped_rag_local",
        policy=policy,
        audit_store=audit,
        request_context=context,
        active_release=release,
    )
    if policy.can_cache:
        cache.set(
            message=request.message,
            entitlement=entitlement,
            scope=policy.retrieval_scope,
            response=response,
            release_id=release.release_id,
        )
    _record_audit(
        audit,
        context,
        stage="response_completed",
        payload={
            "route": response.route,
            "citationCount": len(response.citations),
            "usage": response.usage,
        },
    )
    _record_cost(costs, context, request=request, response=response)
    return response


def answer_message_via_http(
    request: ChatRequest,
    *,
    principal: AuthenticatedPrincipal | None = None,
    clients: HttpAegisServiceClients,
    exact_cache: ExactAnswerCache | None = None,
    audit_store: InMemoryAuditStore | None = None,
    cost_ledger: InMemoryCostLedger | None = None,
    request_context: RequestContext | None = None,
    active_release: ActiveRelease | None = None,
) -> ChatResponse:
    cache = exact_cache or GLOBAL_EXACT_CACHE
    audit = audit_store or GLOBAL_AUDIT_STORE
    costs = cost_ledger or GLOBAL_COST_LEDGER
    context = request_context or new_request_context(caller="assistant-api")
    release = active_release or load_active_release()
    _record_audit(
        audit,
        context,
        stage="request_received",
        payload={
            "tenantId": request.tenant_id,
            "userId": request.user_id,
            "mode": "http",
            "subject": principal.subject if principal else None,
            "releaseMetadata": release.metadata,
        },
        telemetry_client=clients,
    )
    entitlement = clients.resolve_entitlements(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        ui_context=request.ui_context,
    )
    requested_module = infer_requested_module(
        request.message,
        fallback_module=request.ui_context.module if request.ui_context else None,
    )
    intent = infer_intent(request.message)
    requested_permissions = infer_requested_permissions(request.message, requested_module)
    policy = clients.evaluate_policy(
        entitlement=entitlement,
        intent=intent,
        risk=RiskLevel.LOW,
        requested_module=requested_module,
        requested_permissions=requested_permissions,
    )

    if policy.decision != PolicyDecisionValue.ALLOW or policy.retrieval_scope is None:
        response = ChatResponse(
            answer="I cannot answer that with your current access.",
            citations=[],
            confidence=0.0,
            route="denial_or_escalation",
            escalation={"reasons": policy.reasons} if policy.must_escalate else None,
        )
        response = _with_usage(response, input_text=request.message, active_release=release)
        _record_audit(
            audit,
            context,
            stage="response_denied",
            payload={"route": response.route, "usage": response.usage},
            telemetry_client=clients,
        )
        _record_cost(costs, context, request=request, response=response, telemetry_client=clients)
        return response

    clients.build_context(
        session_id=request.session_id,
        message=request.message,
        entitlement=entitlement,
        policy_decision=policy,
        ui_context=request.ui_context,
    )

    cached_response = cache.get(
        message=request.message,
        entitlement=entitlement,
        scope=policy.retrieval_scope,
        release_id=release.release_id,
    )
    if cached_response is not None:
        _record_audit(
            audit,
            context,
            stage="cache_hit",
            payload={"route": cached_response.route, "usage": cached_response.usage},
            telemetry_client=clients,
        )
        _record_cost(
            costs,
            context,
            request=request,
            response=cached_response,
            telemetry_client=clients,
        )
        return cached_response

    retrieval_results = clients.search(
        query=request.message,
        retrieval_scope=policy.retrieval_scope,
        top_k=5,
    )
    if not retrieval_results:
        response = ChatResponse(
            answer="I could not find approved context that matches your request.",
            citations=[],
            confidence=0.0,
            route="retrieval_empty",
            escalation=None,
        )
        response = _with_usage(response, input_text=request.message, active_release=release)
        _record_audit(
            audit,
            context,
            stage="retrieval_empty",
            payload={"route": response.route, "usage": response.usage},
            telemetry_client=clients,
        )
        _record_cost(costs, context, request=request, response=response, telemetry_client=clients)
        return response
    _record_audit(
        audit,
        context,
        stage="retrieval_completed",
        payload={"resultCount": len(retrieval_results), "mode": "http"},
        telemetry_client=clients,
    )

    generation = clients.generate(message=request.message, retrieval_results=retrieval_results)
    verification = clients.verify(
        answer=generation.answer,
        citations=generation.citations,
        retrieval_results=retrieval_results,
        policy_decision=policy,
    )
    if not verification.verified:
        response = ChatResponse(
            answer="I could not verify a safe answer from approved context.",
            citations=[],
            confidence=0.0,
            route="verification_failed",
            escalation={"reasons": verification.reasons},
        )
        response = _with_usage(response, input_text=request.message, active_release=release)
        _record_audit(
            audit,
            context,
            stage="verification_failed",
            payload={"route": response.route, "usage": response.usage},
            telemetry_client=clients,
        )
        _record_cost(costs, context, request=request, response=response, telemetry_client=clients)
        return response

    response = _with_usage(
        ChatResponse(
            answer=generation.answer,
            citations=generation.citations,
            confidence=min(generation.confidence, verification.confidence),
            route="scoped_rag_http",
            escalation=None,
        ),
        input_text=request.message,
        active_release=release,
    )
    if policy.can_cache:
        cache.set(
            message=request.message,
            entitlement=entitlement,
            scope=policy.retrieval_scope,
            response=response,
            release_id=release.release_id,
        )
    _record_audit(
        audit,
        context,
        stage="response_completed",
        payload={
            "route": response.route,
            "citationCount": len(response.citations),
            "usage": response.usage,
        },
        telemetry_client=clients,
    )
    _record_cost(costs, context, request=request, response=response, telemetry_client=clients)
    return response


def _generate_verified_response(
    *,
    request: ChatRequest,
    retrieval_results: list[RetrievalResult],
    route: str,
    policy: PolicyDecision,
    audit_store: InMemoryAuditStore,
    request_context: RequestContext,
    active_release: ActiveRelease,
) -> ChatResponse:
    answer, citations, confidence = generate_answer(
        message=request.message,
        retrieval_results=retrieval_results,
    )
    verification = verify_answer(
        answer=answer,
        citations=citations,
        retrieval_results=retrieval_results,
        policy_decision=policy,
    )
    _record_audit(
        audit_store,
        request_context,
        stage="verification_completed",
        payload={
            "verified": verification.verified,
            "route": route,
            "reasons": verification.reasons,
        },
    )
    if not verification.verified:
        return _with_usage(
            ChatResponse(
                answer="I could not verify a safe answer from approved context.",
                citations=[],
                confidence=0.0,
                route="verification_failed",
                escalation={"reasons": verification.reasons},
            ),
            input_text=request.message,
            active_release=active_release,
        )

    return _with_usage(
        ChatResponse(
            answer=answer,
            citations=citations,
            confidence=min(confidence, verification.confidence),
            route=route,
            escalation=None,
        ),
        input_text=request.message,
        active_release=active_release,
    )


def _with_usage(
    response: ChatResponse,
    *,
    input_text: str,
    active_release: ActiveRelease,
) -> ChatResponse:
    return response.model_copy(
        update={
            "usage": estimate_usage(
                response.route,
                input_text=input_text,
                output_text=response.answer,
            ),
            "release_metadata": active_release.metadata,
        }
    )


def _record_audit(
    audit_store: InMemoryAuditStore,
    request_context: RequestContext,
    *,
    stage: str,
    payload: dict,
    telemetry_client: HttpAegisServiceClients | None = None,
) -> None:
    audit_payload = {"stage": stage, **payload}
    audit_store.record(
        request_context=request_context,
        producer="assistant-api",
        payload=audit_payload,
    )
    if telemetry_client is not None:
        telemetry_client.record_audit(
            request_context=request_context,
            producer="assistant-api",
            payload=audit_payload,
        )


def _record_cost(
    cost_ledger: InMemoryCostLedger,
    request_context: RequestContext,
    *,
    request: ChatRequest,
    response: ChatResponse,
    telemetry_client: HttpAegisServiceClients | None = None,
) -> None:
    metadata = {
        "sessionId": request.session_id,
        "citationCount": len(response.citations),
        "confidence": response.confidence,
        "releaseMetadata": response.release_metadata,
    }
    cost_ledger.record(
        request_context=request_context,
        producer="assistant-api",
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        route=response.route,
        usage=response.usage,
        metadata=metadata,
    )
    if telemetry_client is not None:
        telemetry_client.record_cost(
            request_context=request_context,
            producer="assistant-api",
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            route=response.route,
            usage=response.usage,
            metadata=metadata,
        )
