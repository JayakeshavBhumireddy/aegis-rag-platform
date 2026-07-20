from __future__ import annotations

import re

from aegis_shared.contracts import Citation, PolicyDecision, RetrievalResult, VerificationResult

PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
]


def verify_answer(
    *,
    answer: str,
    citations: list[Citation],
    retrieval_results: list[RetrievalResult],
    policy_decision: PolicyDecision,
) -> VerificationResult:
    citation_ids = {(citation.source_id, citation.chunk_id) for citation in citations}
    result_ids = {(result.source_id, result.chunk_id) for result in retrieval_results}
    citations_valid = bool(citation_ids) and citation_ids.issubset(result_ids)
    grounded = bool(retrieval_results) and any(
        result.text in answer for result in retrieval_results
    )
    pii_safe = not any(pattern.search(answer) for pattern in PII_PATTERNS)
    permission_compliant = policy_decision.can_answer and policy_decision.can_retrieve

    reasons: list[str] = []
    if not citations_valid:
        reasons.append("answer is missing valid citations")
    if not grounded:
        reasons.append("answer is not grounded in retrieved context")
    if not pii_safe:
        reasons.append("answer contains sensitive data pattern")
    if not permission_compliant:
        reasons.append("policy does not allow answer")

    verified = citations_valid and grounded and pii_safe and permission_compliant
    return VerificationResult(
        verified=verified,
        grounded=grounded,
        citationsValid=citations_valid,
        permissionCompliant=permission_compliant,
        piiSafe=pii_safe,
        confidence=0.9 if verified else 0.0,
        reasons=reasons,
    )
