# SLO V1

Status: draft

## Availability

| Component | Target |
|---|---:|
| assistant-api | 99.9% |
| entitlement-service | 99.95% |
| policy-service | 99.95% |
| retrieval-service | 99.9% |
| llm-gateway | 99.5% |

## Latency Targets

| Route | p95 Target |
|---|---:|
| exact cache | 100 ms |
| semantic cache | 250 ms |
| navigation graph | 300 ms |
| precomputed answer | 300 ms |
| scoped RAG small model | 3500 ms |
| scoped RAG strong model | 8000 ms |

## Safety Targets

These are release gates, not soft goals:

```text
PII leakage = 0
cross-tenant leakage = 0
license violation = 0
permission violation = 0
```

