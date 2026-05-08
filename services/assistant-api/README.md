# assistant-api

Public orchestration API for chat requests.

Responsibilities:

- validate request shape
- resolve trace/request IDs
- call auth, entitlement, policy, context, retrieval, LLM gateway, and verification services
- coordinate streaming responses
- return answer, citations, confidence, and escalation metadata

First build target:

- `POST /v1/assistant/messages`
- route through entitlement, policy, router, retrieval, LLM gateway, verifier
