# Cache Isolation V1

Status: draft

Caching improves latency and cost, but unsafe cache keys can cause data leakage.

## Required Cache Key Fields

```text
normalized_question
tenant_scope_or_public_scope
license_hash
permission_hash
product_version
region
language
module_context
prompt_version
policy_version
index_version
```

## Cache Rules

1. Public content can use public cache only when no entitlement-specific details are present.
2. Tenant-scoped answers must include tenant or entitlement scope.
3. Permission-sensitive answers must include permission hash.
4. License-sensitive answers must include license hash.
5. Cached answers must store citation and verification metadata.
6. Cache keys must include the active release ID so promoted prompt, policy,
   guardrail, index, or route changes cannot reuse stale answers.
6. Sensitive answers are not cached in V1.
