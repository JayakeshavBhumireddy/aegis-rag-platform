# Completion Backlog V1

Status: active  
Last updated: 2026-07-20

This backlog tracks what remains after the verified local functional slice.
The goal is to move from local deterministic behavior to benchmarked,
deployable, observable, and production-ready behavior without losing the
security properties that make the platform enterprise-shaped.

## Verified Baseline

Current branch checkpoint:

- branch: `feature/infra-foundation`
- commit: `6598667 Build local AegisRAG platform slice`
- release gate: passed with `68` tests at the checkpoint
- HTTP smoke: passed on 2026-07-20 after the checkpoint

The local slice includes:

- authenticated assistant API
- entitlement, policy, context, retrieval, reranker, LLM gateway, verification,
  observability, ingestion, and eval services
- synthetic enterprise corpus
- local hybrid index artifacts
- release candidate, promote, and rollback metadata
- audit, cost, and feedback events
- generated Helm values and Kubernetes NetworkPolicies from a service catalog
- API, infra, runtime packaging, repo hygiene, config, lint, tests, eval, and
  release registry gates

## Phase 2: Public Retrieval Benchmark

- Add dataset manifests for MS MARCO small and BEIR subsets.
- Add a controlled downloader that records dataset version, checksum, source,
  license, and local path without committing large data.
- Extend ingestion to support public passage formats.
- Add retrieval eval metrics: recall@k, MRR@10, nDCG@k, citation coverage, and
  latency percentiles.
- Add benchmark reports under `data/processed/eval-runs/` or another ignored
  generated-output path.
- Compare baseline local hashing retrieval against a real embedding provider or
  local embedding model behind a replaceable adapter.

## Phase 3: Enterprise Infrastructure

- Expand Terraform from catalog validation into deployable dev modules.
- Add concrete module boundaries for EKS, service accounts, IAM, S3, OpenSearch,
  cache, queues, and secrets.
- Add environment overlays for dev, staging, and prod.
- Add image build and deployment workflow documentation.
- Add Kubernetes manifests or Helm chart values for observability sidecars,
  resource policies, autoscaling, pod disruption budgets, and secrets.

## Phase 4: Scale And Safety

- Add load tests for assistant API and retrieval paths.
- Add degraded-mode tests for dependency outages.
- Add semantic cache design and tests.
- Expand prompt-injection and PII eval datasets.
- Add canary and shadow eval simulation.
- Add tenant isolation tests that intentionally mix tenant, license, product,
  region, and permission scopes.

## Phase 5: Production Readiness

- Finalize service contracts and versioning policy.
- Add CI/CD promotion flow for release candidate to staging to production.
- Add incident runbooks and SLO alert playbooks.
- Add support escalation integration points.
- Add production-grade audit/event fanout.
- Add secrets management and rotation documentation.
- Add threat model updates based on implemented services.

## V2: Agents And MCPs

- Define which workflows need agentic planning and which must remain
  deterministic.
- Add tool and MCP boundaries for safe enterprise actions.
- Add policy-aware tool invocation contracts.
- Add agent evals for planning quality, tool safety, permission compliance, and
  recovery from failed tool calls.
- Keep core RAG retrieval, entitlement, policy, and verification as explicit
  services so agents cannot bypass governance.
