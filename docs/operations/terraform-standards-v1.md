# Terraform Standards V1

Status: draft  
Version: terraform-standards-v1

## Layout

```text
infra/terraform/
  envs/
    dev/
    staging/
    prod/
  modules/
```

## Rules

1. Environments compose modules.
2. Modules do not hardcode environment names.
3. Production state must use a remote backend.
4. All persistent resources require encryption.
5. Public access must be disabled by default.
6. IAM must use least privilege.
7. Destructive changes require explicit review.

## Naming

Use:

```text
aegis-rag-{environment}-{component}
```

Examples:

```text
aegis-rag-dev-data
aegis-rag-prod-opensearch
```

## Required Tags

```text
project = aegis-rag
environment = dev|staging|prod
owner = platform
managed_by = terraform
```

