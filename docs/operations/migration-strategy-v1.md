# Migration Strategy V1

AegisRAG has multiple kinds of state. They should not all use the same migration strategy.

## Relational State

Use Alembic migrations for relational metadata.

Examples:

- tenants
- users
- roles
- permissions
- licenses
- content sources
- release registry
- eval runs
- audit metadata
- cost ledger metadata

Location:

```text
services/*/migrations/
```

or, if shared platform metadata is centralized:

```text
services/platform-metadata/migrations/
```

## Object/Data State

Use object storage versioning and manifests.

Examples:

- raw documents
- parsed documents
- chunks
- embeddings
- eval datasets
- generated benchmark artifacts

Location:

```text
data/catalog/
data/raw/
data/processed/
data/evals/
```

Production target:

- S3 buckets with versioning
- DVC or manifest-based versioning

## Search And Vector Indexes

Indexes should be rebuilt from versioned source artifacts.

Do not treat vector/search indexes as the source of truth.

Track:

- index version
- content version
- embedding model version
- chunker version
- metadata schema version
- build time
- eval score

## Policy And Prompt Versions

Policies and prompts are versioned config artifacts.

Location:

```text
configs/policies/
configs/prompts/
configs/routing/
```

Every answer trace must record the versions used.

