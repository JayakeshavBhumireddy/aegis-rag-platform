# Eval Strategy V1

The platform uses evals as release gates. A prompt, policy, retriever, index, model, or guardrail change cannot be promoted without passing the relevant eval suite.

## Eval Families

| Family | Purpose |
|---|---|
| retrieval | recall, MRR, NDCG, top-k quality |
| reranking | candidate ordering quality |
| grounding | generated answer supported by cited context |
| citation | citations exist and map to allowed chunks |
| navigation | route/path accuracy |
| license | no instructions for unlicensed modules |
| permission | no unauthorized actions or data |
| PII | no sensitive leakage |
| prompt injection | malicious instruction resistance |
| refusal | correct denial/escalation behavior |
| latency | p50/p95/p99 by route |
| cost | route and model budget compliance |

## Hard Gates

```text
PII leakage = 0
cross-tenant leakage = 0
license violation = 0
permission violation = 0
prompt injection success = 0
```

The local synthetic release gate currently enforces:

- license violation rate = 0
- permission violation rate = 0
- PII leakage rate = 0
- prompt injection success rate = 0
- navigation failure rate = 0 for covered synthetic navigation cases
- cost budget violation rate = 0 for covered synthetic routes

These scores are written into the local candidate release metadata as
`scoreSummary`.

## Feedback Mining

Negative user feedback can be converted into reviewable eval candidates through
`POST /v1/evals/feedback/mine`. The miner only uses structured metadata captured
with the feedback event, such as the original question, tenant context,
expected modules, route, and release metadata. Freeform user comments are retained
as feedback records but are not promoted into eval prompts.

Feedback-mined cases are candidates, not automatic gates. A reviewer should
deduplicate them, confirm expected behavior, and merge approved cases into the
relevant eval suite before they affect release promotion.

## Initial Public Dataset Evals

- MS MARCO: recall@k, MRR@10, reranker quality.
- BEIR: cross-domain retrieval robustness.
- Synthetic enterprise product-help corpus: entitlement, navigation, permission, refusal behavior.
