# Observability V1

Status: draft

Every request should be traceable across services.

## Required Trace Fields

- requestId
- traceId
- tenantId
- userId hash
- sessionId hash
- route
- intent
- risk
- policyVersion
- promptVersion
- indexVersion
- modelProvider
- modelName
- cacheResult
- retrievedChunkIds
- guardrailDecision
- verificationResult
- latencyMs
- costUsd

## Metrics

- request count by route
- p50/p95/p99 latency by route
- cache hit rate
- retrieval empty rate
- verification failure rate
- guardrail block rate
- escalation rate
- model cost by tenant
- token usage by route
- error rate by dependency

## Logging Rule

Standard logs must not contain raw sensitive data.

