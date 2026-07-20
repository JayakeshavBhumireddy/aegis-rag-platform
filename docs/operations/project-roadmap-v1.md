# Project Roadmap V1

## Phase 0: Architecture And Governance

- project folder scaffold
- architecture V1
- service inventory
- dataset catalog
- baseline policies
- route config
- prompt V1

## Phase 1: Local Functional Slice

- synthetic corpus
- assistant API skeleton
- entitlement envelope simulation
- policy checks
- exact cache
- navigation graph
- retrieval over synthetic docs
- verifier
- basic evals

Status: implemented and verified by the local release gate and HTTP smoke test.

## Phase 2: Public Retrieval Benchmark

- MS MARCO small subset
- embedding pipeline
- vector and keyword index
- retrieval evals
- reranker service
- latency/cost route metrics

## Phase 3: Enterprise Infrastructure

- EKS deployment skeleton
- Terraform modules
- ElastiCache
- OpenSearch Serverless
- S3 data lake layout
- SQS/EventBridge pipelines
- observability stack

## Phase 4: Scale And Safety

- MS MARCO 1M subset
- load testing
- semantic cache
- degraded mode
- prompt injection tests
- PII leakage tests
- canary/shadow eval simulation

## Phase 5: Production Readiness

- service contracts finalized
- CI/CD release gates
- release registry
- audit pipeline
- support escalation integration
- incident runbooks
