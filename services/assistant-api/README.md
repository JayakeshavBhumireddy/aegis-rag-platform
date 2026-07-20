# assistant-api

Public orchestration API for chat requests.

Responsibilities:

- validate request shape
- authenticate caller identity
- resolve trace/request IDs
- call auth, entitlement, policy, context, retrieval, LLM gateway, and verification services
- coordinate streaming responses
- return answer, citations, confidence, and escalation metadata

First build target:

- `POST /v1/assistant/messages`
- route through entitlement, policy, router, retrieval, LLM gateway, verifier
- require `Authorization: Bearer <local-dev-token>` and fail closed on identity mismatch
