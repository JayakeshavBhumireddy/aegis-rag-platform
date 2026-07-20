from __future__ import annotations

from aegis_shared.contracts import Citation, RetrievalScope, RiskLevel
from entitlement_service.resolver import InMemoryEntitlementStore, resolve_entitlement_envelope
from policy_service.evaluator import evaluate_policy
from retrieval_service.search import search_corpus
from verification_service.verifier import verify_answer


def test_verifies_grounded_cited_answer() -> None:
    entitlement = resolve_entitlement_envelope("tenant_123", "user_123", InMemoryEntitlementStore())
    policy = evaluate_policy(
        entitlement=entitlement,
        intent="navigation",
        risk=RiskLevel.LOW,
        requested_module="Billing",
    )
    assert isinstance(policy.retrieval_scope, RetrievalScope)
    results = search_corpus(query="monthly billing", retrieval_scope=policy.retrieval_scope)
    citation = Citation(
        sourceId=results[0].source_id,
        chunkId=results[0].chunk_id,
        title=results[0].title,
    )

    verification = verify_answer(
        answer=results[0].text,
        citations=[citation],
        retrieval_results=results,
        policy_decision=policy,
    )

    assert verification.verified is True


def test_blocks_pii_pattern() -> None:
    entitlement = resolve_entitlement_envelope("tenant_123", "user_123", InMemoryEntitlementStore())
    policy = evaluate_policy(
        entitlement=entitlement,
        intent="navigation",
        risk=RiskLevel.LOW,
        requested_module="Billing",
    )

    verification = verify_answer(
        answer="Customer SSN is 123-45-6789.",
        citations=[],
        retrieval_results=[],
        policy_decision=policy,
    )

    assert verification.verified is False
    assert verification.pii_safe is False
