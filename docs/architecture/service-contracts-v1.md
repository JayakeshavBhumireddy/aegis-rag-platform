# Service Contracts V1

Status: draft  
Version: service-contracts-v1

This document defines the first service contracts for AegisRAG. These contracts are intentionally technology-neutral so the implementation can evolve without changing the platform behavior.

The machine-checkable route surface lives in:

```text
docs/architecture/api-surface-v1.json
```

`make validate-api` imports each FastAPI app and verifies implemented public
routes match that manifest.

## Common Requirements

Every service request must carry:

```json
{
  "requestId": "req_01",
  "traceId": "trace_01",
  "timestamp": "2026-05-08T00:00:00Z",
  "caller": "assistant-api",
  "contractVersion": "v1"
}
```

Every service response must return:

```json
{
  "requestId": "req_01",
  "status": "ok",
  "warnings": [],
  "version": "service-version"
}
```

Security-critical services must fail closed.

## assistant-api

Endpoint:

```text
POST /v1/assistant/messages
```

Input:

```json
{
  "message": "How do I submit this workflow?",
  "tenantId": "tenant_123",
  "userId": "user_123",
  "sessionId": "session_123",
  "uiContext": {
    "module": "Billing",
    "page": "Monthly Submission"
  }
}
```

Output:

```json
{
  "answer": "Use the Billing area, then open Monthly Submission.",
  "citations": [],
  "confidence": 0.91,
  "route": "navigation_graph",
  "escalation": null,
  "usage": {
    "estimatedLatencyMs": 80,
    "estimatedCostUsd": 0.0001,
    "provider": "local-navigation-graph",
    "inputTokens": 8,
    "outputTokens": 13,
    "route": "navigation_graph",
    "currency": "USD"
  },
  "releaseMetadata": {
    "releaseId": "release_123",
    "status": "prod",
    "appVersion": "0.1.0",
    "contentVersion": "content-v1",
    "indexVersion": "index-v1",
    "promptVersion": "answer-prompt-v1",
    "policyVersion": "policy-baseline-v1",
    "guardrailVersion": "guardrails-local-v1",
    "routerConfigVersion": "inference-routes-v1"
  }
}
```

## entitlement-service

Endpoint:

```text
POST /v1/entitlements/resolve
```

Input:

```json
{
  "tenantId": "tenant_123",
  "userId": "user_123",
  "uiContext": {
    "module": "Billing",
    "page": "Monthly Submission"
  }
}
```

Output:

```json
{
  "entitlementEnvelope": {
    "tenantId": "tenant_123",
    "userId": "user_123",
    "region": "us",
    "productVersion": "2026.2",
    "licensedModules": ["Billing", "Reports"],
    "enabledFeatures": ["MonthlySubmission"],
    "role": "TenantAdmin",
    "permissions": ["Billing.View", "Billing.Submit"],
    "licenseHash": "lic_hash",
    "permissionHash": "perm_hash",
    "dataAccessMode": "product_guidance_only"
  }
}
```

## observability-service

Endpoints:

```text
POST /v1/audit/records
GET /v1/audit/records
POST /v1/cost/events
GET /v1/cost/events
POST /v1/feedback/events
GET /v1/feedback/events
```

Audit input:

```json
{
  "request_context": {
    "requestId": "req_01",
    "traceId": "trace_01",
    "timestamp": "2026-05-08T00:00:00Z",
    "caller": "assistant-api",
    "contractVersion": "v1"
  },
  "producer": "assistant-api",
  "payload": {
    "stage": "response_completed",
    "route": "scoped_rag_http"
  }
}
```

Cost input:

```json
{
  "request_context": {
    "requestId": "req_01",
    "traceId": "trace_01",
    "timestamp": "2026-05-08T00:00:00Z",
    "caller": "assistant-api",
    "contractVersion": "v1"
  },
  "producer": "assistant-api",
  "tenantId": "tenant_123",
  "userId": "user_123",
  "route": "scoped_rag_http",
  "usage": {
    "estimatedCostUsd": 0.002,
    "currency": "USD"
  },
  "metadata": {
    "sessionId": "session_123",
    "citationCount": 1,
    "confidence": 0.9
  }
}
```

Feedback input:

```json
{
  "request_context": {
    "requestId": "req_01",
    "traceId": "trace_01",
    "timestamp": "2026-05-08T00:00:00Z",
    "caller": "assistant-ui",
    "contractVersion": "v1"
  },
  "producer": "assistant-ui",
  "tenantId": "tenant_123",
  "userId": "user_123",
  "sessionId": "session_123",
  "messageId": "message_123",
  "rating": 1,
  "comment": "Helpful answer.",
  "categories": ["grounded"],
  "metadata": {
    "route": "scoped_rag_http"
  }
}
```

Output:

```json
{
  "event": {
    "eventId": "evt_01",
    "eventType": "aegis.cost.event.recorded",
    "eventVersion": "v1",
    "occurredAt": "2026-05-08T00:00:00Z",
    "requestId": "req_01",
    "traceId": "trace_01",
    "producer": "assistant-api",
    "payload": {}
  }
}
```

Failure:

- If the envelope cannot be resolved, the assistant must not answer.

## eval-service

Endpoints:

```text
POST /v1/evals/synthetic-enterprise/run
POST /v1/evals/feedback/mine
POST /v1/releases/local/candidate
POST /v1/releases/local/promote
POST /v1/releases/local/rollback
```

Feedback mining input:

```json
{
  "events": [
    {
      "eventId": "evt_feedback",
      "eventType": "aegis.feedback.received",
      "eventVersion": "v1",
      "occurredAt": "2026-05-08T00:00:00Z",
      "requestId": "req_feedback",
      "traceId": "trace_feedback",
      "producer": "assistant-ui",
      "payload": {
        "rating": -1,
        "categories": ["citation_issue"],
        "metadata": {
          "question": "Where do I submit monthly billing?",
          "route": "scoped_rag_http",
          "tenantContext": {
            "licensedModules": ["Billing"],
            "permissions": ["Billing.View"],
            "dataAccessMode": "product_guidance_only"
          },
          "expectedModules": ["Billing"],
          "releaseMetadata": {
            "releaseId": "release_123"
          }
        }
      }
    }
  ]
}
```

Feedback mining output:

```json
{
  "totalFeedbackEvents": 1,
  "candidateCount": 1,
  "skippedCount": 0,
  "candidates": [
    {
      "id": "FB-evt_feedback",
      "question": "Where do I submit monthly billing?",
      "tenantContext": {},
      "expectedBehavior": "answer",
      "expectedModules": ["Billing"],
      "forbiddenContent": [],
      "mustCiteSource": true,
      "riskLevel": "medium",
      "sourceFeedback": {
        "eventId": "evt_feedback",
        "requestId": "req_feedback",
        "traceId": "trace_feedback",
        "categories": ["citation_issue"],
        "route": "scoped_rag_http",
        "releaseId": "release_123"
      }
    }
  ],
  "skipped": []
}

```

Feedback-mined cases are reviewable candidates. They are not automatically
merged into release-gating suites.

## policy-service

Endpoint:

```text
POST /v1/policy/evaluate
```

Input:

```json
{
  "entitlementEnvelope": {},
  "intent": "workflow_help",
  "risk": "low",
  "requestedModule": "Billing"
}
```

Output:

```json
{
  "decision": "allow",
  "canRetrieve": true,
  "canAnswer": true,
  "canCache": true,
  "mustEscalate": false,
  "retrievalScope": {
    "tenantId": "tenant_123",
    "modules": ["Billing"],
    "permissions": ["Billing.View", "Billing.Submit"],
    "productVersion": "2026.2",
    "trustLevel": "approved"
  },
  "reasons": []
}
```

Failure:

- If policy evaluation fails, deny or escalate.

## context-service

Endpoint:

```text
POST /v1/context/build
```

Input:

```json
{
  "sessionId": "session_123",
  "message": "What do I do next?",
  "entitlementEnvelope": {},
  "policyDecision": {},
  "uiContext": {}
}
```

Output:

```json
{
  "contextPack": {
    "recentTurns": [],
    "sessionSummary": null,
    "safeUserMemory": [],
    "tenantContext": {},
    "redactions": []
  }
}
```

## retrieval-service

Endpoint:

```text
POST /v1/retrieval/search
```

Input:

```json
{
  "query": "monthly submission workflow",
  "retrievalScope": {},
  "topK": 20,
  "retrievalMode": "hybrid_rerank"
}
```

Output:

```json
{
  "results": [
    {
      "chunkId": "chunk_123",
      "sourceId": "source_123",
      "title": "Monthly Submission Guide",
      "text": "Approved context snippet.",
      "score": 0.82,
      "metadata": {
        "module": "Billing",
        "trustLevel": "approved"
      }
    }
  ]
}
```

## reranker-service

Endpoint:

```text
POST /v1/rerank
```

Input:

```json
{
  "query": "monthly submission workflow",
  "topK": 10,
  "candidates": [
    {
      "chunkId": "chunk_123",
      "sourceId": "source_123",
      "title": "Monthly Submission Guide",
      "text": "Approved context snippet.",
      "score": 0.82,
      "metadata": {
        "module": "Billing",
        "trustLevel": "approved"
      }
    }
  ]
}
```

Output:

```json
{
  "results": [
    {
      "chunkId": "chunk_123",
      "sourceId": "source_123",
      "title": "Monthly Submission Guide",
      "text": "Approved context snippet.",
      "score": 0.91,
      "metadata": {
        "module": "Billing",
        "trustLevel": "approved",
        "reranker": {
          "model": "local-lexical-reranker-v1",
          "inputScore": 0.82
        }
      }
    }
  ]
}
```

## llm-gateway

Endpoint:

```text
POST /v1/llm/generate
```

Input:

```json
{
  "route": "scoped_rag_small_model",
  "promptVersion": "answer-prompt-v1",
  "messages": [],
  "maxOutputTokens": 700,
  "temperature": 0.1
}
```

Output:

```json
{
  "draftAnswer": "Generated answer.",
  "model": "selected-model",
  "provider": "selected-provider",
  "inputTokens": 1200,
  "outputTokens": 180,
  "costUsd": 0.002
}
```

## verification-service

Endpoint:

```text
POST /v1/verification/check
```

Input:

```json
{
  "draftAnswer": "Generated answer.",
  "citations": [],
  "entitlementEnvelope": {},
  "policyDecision": {},
  "retrievedChunks": []
}
```

Output:

```json
{
  "verified": true,
  "grounded": true,
  "citationsValid": true,
  "permissionCompliant": true,
  "piiSafe": true,
  "confidence": 0.91,
  "reasons": []
}
```
