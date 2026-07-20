# Release Process V1

Status: draft

## Release Inputs

Every release candidate must declare:

- app version
- content version
- chunker version
- embedding model version
- index version
- prompt version
- policy version
- guardrail version
- router config version
- eval dataset version

## Promotion Flow

```text
dev
-> CI eval gate
-> staging
-> internal dogfood
-> shadow
-> canary
-> tenant allowlist
-> production
```

## Rollback

Rollback must support reverting:

- service image
- prompt version
- policy version
- index version
- router config
- guardrail version

## Local Release Gate

The local release gate writes a candidate release record to:

```text
data/processed/release-registry/local-candidate.json
```

The generated candidate records the app, content, chunker, embedding, index,
prompt, policy, guardrail, router, eval, service image, and rollback metadata
required for later promotion workflows.

Local promotion writes:

```text
data/processed/release-registry/local-active.json
```

If a prior active release exists, it is preserved as:

```text
data/processed/release-registry/local-rollback.json
```

Local rollback restores `local-rollback.json` to active status and records the
rolled-back release metadata in the rollback file. The same hard release gates
are validated for candidate registration, promotion, and rollback.

Local eval-service endpoints:

- `POST /v1/releases/local/candidate`
- `POST /v1/releases/local/promote`
- `POST /v1/releases/local/rollback`

Local Make targets:

- `make release-candidate`
- `make release-promote`
- `make release-rollback`

`make http-smoke` creates and promotes an isolated smoke-test release, starts
the local service graph, and verifies assistant-api returns that active release
metadata in the HTTP response and cost telemetry.
