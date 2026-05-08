# Service Contracts V1

Status: draft  
Version: service-contracts-v1

This document defines the first service contracts for AegisRAG. These contracts are intentionally technology-neutral so the implementation can evolve without changing the platform behavior.

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
  "escalation": null
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

Failure:

- If the envelope cannot be resolved, the assistant must not answer.

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
  "retrievalMode": "hybrid"
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
POST /v1/verification/answer
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

