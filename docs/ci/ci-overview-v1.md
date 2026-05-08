# CI Overview V1

Status: draft

The CI skeleton protects the repo before service code exists. It checks repository hygiene, config syntax, Terraform formatting/validation, security docs, and eval contract basics.

## Workflows

| Workflow | Purpose |
|---|---|
| `ci.yml` | general repo checks |
| `terraform.yml` | Terraform format and dev validation |
| `security.yml` | baseline secret/security doc checks |
| `evals.yml` | eval/config/data contract checks |

## Local Equivalent

Run:

```bash
make check
make tf-fmt
make tf-validate-dev
make synthetic-data
```

On Windows PowerShell, the equivalent validation entry points are:

```powershell
.\scripts\validation\check.ps1
.\scripts\data\generate_synthetic_corpus.ps1
```

## Current Limitations

- YAML validation is lightweight until we add a real YAML parser.
- Terraform validation requires Terraform installed.
- Synthetic data generation requires Python installed.
- Docker Compose validation requires Docker installed.
