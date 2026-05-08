# Tooling Recommendations V1

These are the recommended tools for AegisRAG. The goal is enterprise readiness without making the local development loop painful.

## Languages

| Area | Recommendation | Reason |
|---|---|---|
| services | Python 3.12 | strong AI/data ecosystem, FastAPI, eval tooling |
| infra | Terraform | cloud-neutral infrastructure as code |
| platform deployment | Helm + Kubernetes YAML | repeatable EKS deployments |
| scripts | Python + Makefile | clear automation |

## Python Package Manager

Recommendation: `uv`.

Why:

- fast dependency resolution
- lockfile support
- good monorepo ergonomics
- works well for Python services and tooling

Fallback:

- Poetry is also acceptable, but `uv` is simpler and faster for this project.

## Database Migrations

Recommendation: Alembic for relational database migrations.

Use migrations for:

- tenants
- users/roles/permissions metadata
- content registry
- release registry
- cost ledger metadata
- eval run metadata

Do not use migrations for:

- raw documents
- large chunk files
- vector indexes
- generated embeddings

Those belong in object storage and index/version registries.

## Local Runtime

Recommendation:

- Docker Compose for local dependencies.
- Native Python service execution for fast iteration.

Local dependencies:

- Postgres
- Redis/Valkey
- OpenSearch
- Qdrant optional
- OpenTelemetry Collector

## Cloud Target

Recommended enterprise target:

- EKS
- ElastiCache for Valkey
- OpenSearch Serverless
- S3
- DynamoDB/Aurora
- SQS/EventBridge
- Amazon Verified Permissions
- Bedrock through LLM Gateway
- SageMaker or Triton for rerankers/classifiers

