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

