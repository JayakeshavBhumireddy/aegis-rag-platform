# Event Contracts V1

Status: draft  
Version: event-contracts-v1

Events are used for async work such as ingestion, evals, feedback, audit fanout, cost tracking, and release promotion.

## Common Event Envelope

```json
{
  "eventId": "evt_01",
  "eventType": "aegis.ingestion.requested",
  "eventVersion": "v1",
  "occurredAt": "2026-05-08T00:00:00Z",
  "requestId": "req_01",
  "traceId": "trace_01",
  "producer": "ingestion-service",
  "payload": {}
}
```

## Events

| Event Type | Producer | Consumer | Purpose |
|---|---|---|---|
| `aegis.ingestion.requested` | ingestion-service | ingestion workers | ingest source manifest |
| `aegis.index.build.completed` | ingestion-service | eval-service | run index evals |
| `aegis.eval.run.completed` | eval-service | release process | decide promotion |
| `aegis.feedback.received` | assistant-api | eval/content workflows | improve content/evals |
| `aegis.audit.record.created` | services | audit pipeline | durable audit fanout |
| `aegis.cost.event.recorded` | assistant-api | cost pipeline | tenant and route cost ledger |
| `aegis.release.promoted` | release process | all services | update active versions |

## Ingestion Requested Payload

```json
{
  "datasetId": "synthetic-enterprise-product-help",
  "sourceManifestVersion": "source-manifest-v1",
  "targetEnvironment": "dev",
  "requestedBy": "user_or_pipeline"
}
```

## Cost Event Payload

```json
{
  "tenantId": "tenant_123",
  "userId": "user_123",
  "route": "scoped_rag_http",
  "usage": {
    "estimatedLatencyMs": 900,
    "estimatedCostUsd": 0.002,
    "provider": "local-http-rag",
    "inputTokens": 24,
    "outputTokens": 12,
    "route": "scoped_rag_http",
    "currency": "USD"
  },
  "metadata": {
    "sessionId": "session_123",
    "citationCount": 1,
    "confidence": 0.9
  }
}
```

## Eval Completed Payload

```json
{
  "evalRunId": "eval_123",
  "candidateVersion": {
    "contentVersion": "content-v1",
    "indexVersion": "index-v1",
    "promptVersion": "answer-prompt-v1",
    "policyVersion": "policy-baseline-v1"
  },
  "passed": true,
  "scores": {
    "licenseViolationRate": 0,
    "permissionViolationRate": 0,
    "piiLeakageRate": 0,
    "groundedAnswerRate": 0.96
  }
}
```
