# RAG Architecture Learning Map V1

Status: active  
Last updated: 2026-07-20

This project is both a platform and a study lab. The aim is to understand every
important line by connecting code to architecture decisions: why the service
exists, what risk it controls, what contract it exposes, and how it would scale.

## How To Study A Subsystem

For each subsystem, use the same loop:

1. Read the public contract in `docs/architecture/service-contracts-v1.md`.
2. Read the shared model in `packages/aegis_shared/contracts.py`.
3. Read the FastAPI route in `services/<service>/src/.../main.py`.
4. Read the business logic module beside it.
5. Read the tests and explain what behavior they prove.
6. Run the focused tests.
7. Draw the inputs, decisions, outputs, and failure modes.
8. Ask what would change for production scale.

## Code Reading Order

1. Shared contracts:
   - `packages/aegis_shared/contracts.py`
   - `packages/aegis_shared/runtime.py`
2. Request entry:
   - `services/assistant-api/src/assistant_api/main.py`
   - `services/assistant-api/src/assistant_api/auth.py`
   - `services/auth-service/src/auth_service/local_tokens.py`
3. Orchestration:
   - `services/assistant-api/src/assistant_api/orchestrator.py`
   - `services/assistant-api/src/assistant_api/service_clients.py`
4. Governance:
   - `services/entitlement-service/src/entitlement_service/resolver.py`
   - `services/policy-service/src/policy_service/evaluator.py`
5. Retrieval pipeline:
   - `services/ingestion-service/src/ingestion_service/pipeline.py`
   - `services/retrieval-service/src/retrieval_service/index.py`
   - `services/retrieval-service/src/retrieval_service/search.py`
   - `services/reranker-service/src/reranker_service/ranker.py`
6. Generation and verification:
   - `services/llm-gateway/src/llm_gateway/generator.py`
   - `services/verification-service/src/verification_service/verifier.py`
7. Observability and release:
   - `services/observability-service/src/observability_service/event_repository.py`
   - `services/eval-service/src/eval_service/runner.py`
   - `services/eval-service/src/eval_service/release_registry.py`
8. Deployment contracts:
   - `infra/service-catalog/aegis-services.json`
   - `scripts/validation/validate_api_contracts.py`
   - `scripts/validation/validate_infra_contracts.py`
   - `scripts/validation/run_release_gate.py`

## Architecture Questions To Practice

- Where is tenant isolation enforced?
- Where is permission scope created, preserved, and checked?
- Why does assistant-api orchestrate instead of each service calling everything?
- Why is the LLM gateway the only service allowed to call a model?
- What does verification prove, and what does it not prove?
- What metadata must travel with an answer for audit and rollback?
- Which failures should deny, escalate, retry, or fail open?
- What changes when retrieval moves from synthetic docs to MS MARCO or BEIR?
- What changes when local stores become Postgres, OpenSearch, S3, queues, and
  service meshes?

## Exercises

1. Trace a successful billing question from HTTP request to answer.
2. Trace an unlicensed inventory question and explain where it is denied.
3. Add one new synthetic document and update the eval that proves it works.
4. Add one negative feedback event and convert it into an eval candidate.
5. Break one service dependency and explain the expected degraded behavior.
6. Design the same architecture with agents, then list the governance boundaries
   that agents must not bypass.

## Mental Model

Enterprise RAG is not just retrieval plus a model. It is a governed pipeline:

```text
identity
-> entitlement
-> policy
-> scoped context
-> scoped retrieval
-> optional reranking
-> controlled generation
-> verification
-> audited response
-> eval and release feedback loop
```

V2 agents and MCPs should sit on top of this governed pipeline, not replace it.
