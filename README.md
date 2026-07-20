# AegisRAG Platform

Status: initial project scaffold  
Date: 2026-05-07

This project contains the enterprise-scale architecture, service boundaries, data catalog, configs, infra placeholders, and evaluation structure for AegisRAG, a tenant-aware enterprise RAG platform.

The goal is to build a production-grade AI platform, not a simple RAG demo. The platform is designed for:

- multi-tenant isolation
- license and permission scoped retrieval
- high throughput and low latency
- deterministic security controls
- safe context, memory, and state
- model/provider abstraction
- continuous evals and release gates
- fallback and degraded-mode operation

## Folder Structure

```text
aegis-rag-platform/
  docs/
    architecture/     system architecture and service designs
    decisions/        architecture decision records
    security/         threat model, leakage controls, policy model
    operations/       runbooks, SLOs, deployment modes
    evals/            eval strategy and release gates
  data/
    catalog/          dataset manifests and governance metadata
    raw/              local raw dataset landing area
    processed/        parsed/chunked/enriched data
    indexes/          generated index artifacts or index manifests
    evals/            golden, adversarial, regression eval datasets
  configs/
    environments/     dev/stage/prod configs
    policies/         policy and entitlement rules
    prompts/          versioned prompt templates
    routing/          inference route configs
  services/
    assistant-api/
    entitlement-service/
    policy-service/
    context-service/
    retrieval-service/
    reranker-service/
    llm-gateway/
    verification-service/
    ingestion-service/
    eval-service/
    observability-service/
  infra/
    terraform/
    kubernetes/
    helm/
  scripts/
  tests/
```

## Initial Dataset Strategy

Use public datasets first. Do not use customer or tenant data for the showcase.

Recommended sequence:

1. MS MARCO passage ranking subset for local retrieval/eval development.
2. MS MARCO full passage corpus for large-scale retrieval benchmarking.
3. BEIR datasets for cross-domain retrieval quality.
4. Wikipedia subset for large general knowledge indexing.
5. Synthetic enterprise product/help-navigation content for entitlement and policy simulation.

Large datasets should be downloaded into controlled storage, not committed to source control.

## Service Spine

```text
Edge Security
-> API Gateway
-> Auth
-> Tenant Resolver
-> Entitlement Service
-> Policy Engine
-> Intent/Risk/PII Classification
-> Inference Router
-> Cache / Navigation Graph / FAQ / Scoped RAG
-> LLM Gateway
-> Answer Verification
-> Output Guardrails
-> Audit + Cost + Evals + Feedback
```

## Recommended Enterprise Stack

- AWS CloudFront, WAF, Shield
- EKS
- Amazon Verified Permissions / Cedar
- Aurora PostgreSQL and DynamoDB
- ElastiCache for Valkey
- OpenSearch Serverless
- S3
- EventBridge and SQS
- SageMaker or NVIDIA Triton for ONNX/TensorRT serving
- Bedrock through an LLM Gateway, with provider fallback
- Bedrock Guardrails plus deterministic verification
- OpenTelemetry, CloudWatch, Datadog/Grafana
- Terraform and Argo CD

## Next Steps

1. Finalize service contracts.
2. Add dataset download manifests and ingestion jobs.
3. Define eval schemas.
4. Create Terraform module skeletons.
5. Add API skeletons for core services.

## Local Functional Slice

The repository now includes a deterministic local Phase 1 slice over the
synthetic enterprise corpus:

```text
assistant-api
-> auth-service
-> entitlement-service
-> policy-service
-> context-service
-> retrieval-service
-> reranker-service
-> llm-gateway
-> verification-service
-> observability-service
-> eval-service
```

This slice is intentionally local and safe:

- entitlement resolution uses an in-memory source
- assistant-api requires a local dev bearer token and checks it against body identity
- entitlement-service can resolve from either in-memory fixtures or metadata tables
- policy denies unlicensed modules and unsafe/customer-data intents
- ingestion publishes deterministic chunks and a local hybrid index
- exact cache keys include tenant, user, license, permission, product, and scope
- navigation graph answers route requests before RAG when a permitted path matches
- retrieval uses local hybrid keyword/vector artifacts with scoped fallback
- retrieval can opt into local lexical reranking with explainable ranking signals
- the LLM gateway uses a deterministic context extractor, not an external model
- verification requires grounded, cited, permission-compliant, PII-safe answers
- assistant-api records local audit events with request and trace context
- assistant responses include deterministic local usage estimates for latency,
  cost, provider, and token counts
- observability-service records in-memory cost events per assistant response
- observability-service accepts in-memory feedback events for answer quality loops
- local compose config uses a SQLite observability event store for restart-safe
  audit, cost, and feedback envelopes
- fail-closed API errors use the shared error contract shape
- eval-service runs the synthetic license/navigation gate
- release gate writes a local candidate release record with rollback metadata
- local candidate releases enforce zero license, permission, PII, and prompt-injection violations
- local candidate releases enforce zero cost-budget violations for covered routes

Run the full local release gate:

```bash
make release-gate
```

Manage the local release pointer:

```bash
make release-candidate
make release-promote
make release-rollback
```

The gate writes generated release metadata to:

```text
data/processed/release-registry/local-candidate.json
```

The release record includes app, content, chunker, embedding, index, prompt,
policy, guardrail, router, eval, service image, status, and rollback fields.
The local release registry can also promote a validated candidate into
`data/processed/release-registry/local-active.json` and preserve the previous
active release in `data/processed/release-registry/local-rollback.json`.
assistant-api reads `local-active.json` by default, includes active release
metadata in responses and audit/cost events, and scopes exact-cache entries by
release ID. Set `AEGIS_ACTIVE_RELEASE_PATH` to point at a different active
release record.

Or run the individual checks:

```bash
uv run python -m ingestion_service.pipeline
uv run pytest -q
uv run ruff check .
python3 scripts/validation/validate_configs.py
python3 scripts/validation/check_repo_hygiene.py
python3 scripts/validation/validate_infra_contracts.py
uv run python scripts/validation/validate_api_contracts.py
```

Regenerate deployment values from the service catalog:

```bash
make helm-values
make k8s-policies
```

Run the local service stack:

```bash
make local-up
make stack-check
```

Run a no-Docker HTTP smoke test:

```bash
make http-smoke
```

This starts the FastAPI services as local subprocesses, waits for health
endpoints, sends an authenticated assistant request through HTTP dependency
mode, verifies a promoted active release is consumed by assistant-api, verifies
audit/cost events reach SQLite-backed observability, and then tears the
processes down.

The compose stack uses a shared Python service image and exposes:

| Service | URL |
|---|---|
| assistant-api | `http://localhost:8000` |
| auth-service | `http://localhost:8010` |
| entitlement-service | `http://localhost:8011` |
| policy-service | `http://localhost:8012` |
| context-service | `http://localhost:8013` |
| retrieval-service | `http://localhost:8014` |
| llm-gateway | `http://localhost:8015` |
| verification-service | `http://localhost:8016` |
| observability-service | `http://localhost:8017` |
| ingestion-service | `http://localhost:8018` |
| eval-service | `http://localhost:8019` |
| reranker-service | `http://localhost:8020` |

Run the assistant API locally:

```bash
PYTHONPATH=packages:services/entitlement-service/src:services/ingestion-service/src:services/policy-service/src:services/context-service/src:services/retrieval-service/src:services/reranker-service/src:services/llm-gateway/src:services/verification-service/src:services/assistant-api/src:services/eval-service/src \
  uv run uvicorn assistant_api.main:app --reload
```

By default, assistant-api uses the in-process local implementation. To exercise
service-to-service HTTP clients, run the dependent services separately and set:

```bash
export AEGIS_ASSISTANT_DEPENDENCY_MODE=http
export AEGIS_ENTITLEMENT_URL=http://localhost:8011
export AEGIS_POLICY_URL=http://localhost:8012
export AEGIS_CONTEXT_URL=http://localhost:8013
export AEGIS_RETRIEVAL_URL=http://localhost:8014
export AEGIS_LLM_GATEWAY_URL=http://localhost:8015
export AEGIS_VERIFICATION_URL=http://localhost:8016
export AEGIS_OBSERVABILITY_URL=http://localhost:8017
```

Local observability:

- `observability-service` exposes `POST /v1/audit/records`
- `observability-service` exposes `POST /v1/cost/events`
- `observability-service` exposes `POST /v1/feedback/events`
- assistant-api emits audit stages for request receipt, entitlement, policy,
  cache hits, retrieval, verification, denial, and completion
- assistant-api records one cost event per returned answer with tenant, user,
  route, usage, session, citation count, and confidence metadata
- in HTTP dependency mode, assistant-api also posts audit and cost events to
  observability-service using fail-open telemetry calls
- `AEGIS_OBSERVABILITY_STORE_MODE=sqlite` and
  `AEGIS_OBSERVABILITY_SQLITE_PATH=...` enable durable local observability
- feedback events can record answer ratings, comments, categories, and route
  metadata for later eval dataset mining
- the local implementation uses an in-memory audit store; production fanout can
  replace this with EventBridge/SQS, an audit ledger, or a billing ledger
  without changing the event envelope

Example request:

```bash
TOKEN=$(PYTHONPATH=packages:services/auth-service/src \
  uv run python -c 'from auth_service.local_tokens import create_local_dev_token; print(create_local_dev_token(tenant_id="tenant_123", user_id="user_123"))')

curl -s http://127.0.0.1:8000/v1/assistant/messages \
  -H 'content-type: application/json' \
  -H "authorization: Bearer ${TOKEN}" \
  -d '{
    "message": "Where do I submit monthly billing?",
    "tenantId": "tenant_123",
    "userId": "user_123",
    "sessionId": "session_123",
    "uiContext": {"module": "Billing", "page": "Monthly Submission"}
  }'
```
