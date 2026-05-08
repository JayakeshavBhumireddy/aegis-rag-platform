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

## Initial Public Dataset Evals

- MS MARCO: recall@k, MRR@10, reranker quality.
- BEIR: cross-domain retrieval robustness.
- Synthetic enterprise product-help corpus: entitlement, navigation, permission, refusal behavior.
