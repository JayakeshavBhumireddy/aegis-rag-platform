# Threat Model V1

Status: draft

## Primary Assets

- tenant data
- entitlement and permission data
- product/content indexes
- prompts and policy configs
- model responses
- audit logs
- API credentials and provider keys
- eval datasets and results

## Main Threats

| Threat | Example | Control |
|---|---|---|
| cross-tenant leakage | tenant A receives tenant B answer | entitlement-scoped retrieval, cache keys, verifier |
| unlicensed content exposure | answer gives steps for unavailable module | policy filters, output guardrails |
| permission bypass | user receives admin-only workflow | policy engine, verifier |
| prompt injection | user asks model to ignore rules | classifier, prompt isolation, verifier |
| poisoned content | malicious docs enter index | content approval, source allowlist, scan |
| PII leakage | response includes sensitive data | PII scanner, redaction, data-access mode |
| cache leakage | cached answer reused across scopes | scoped cache keys |
| model provider outage | request path fails | circuit breakers, fallback routes |
| audit loss | incident cannot be reconstructed | durable audit queue and storage |

## Security Boundary

The LLM is not a security boundary.

Required deterministic boundaries:

- authentication
- entitlement resolution
- policy evaluation
- retrieval filtering
- cache scope validation
- answer verification
- audit logging

## Fail-Closed Dependencies

- entitlement-service
- policy-service
- PII scanner for sensitive flows
- verification-service for high-risk flows

