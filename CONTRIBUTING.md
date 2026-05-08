# Contributing To AegisRAG

This project is built as an enterprise platform. We make small, explainable changes and keep architecture, infra, and code traceable.

## Working Style

1. Make one meaningful change at a time.
2. Keep commits small and named by purpose.
3. Update docs/configs with code when behavior changes.
4. Prefer explicit interfaces over hidden coupling.
5. Never commit secrets, raw large datasets, generated indexes, or credentials.

## Branch Naming

Use short, descriptive branch names:

```text
feature/infra-foundation
feature/terraform-networking
feature/local-dev-stack
feature/service-contracts
feature/ingestion-pipeline
fix/policy-cache-key
docs/eval-strategy
```

## Commit Style

Use conventional commit prefixes:

```text
docs: add platform roadmap
infra: scaffold terraform modules
config: add inference routing baseline
test: add policy eval cases
feat: add entitlement service skeleton
fix: correct cache scope validation
```

## Review Checklist

Before a commit:

- Does the change have a single clear purpose?
- Did we avoid committing data, secrets, or generated indexes?
- Are service contracts/configs updated if needed?
- Are security assumptions documented?
- Is there a small test or validation path?
