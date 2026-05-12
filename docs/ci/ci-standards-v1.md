# CI Standards V1

Status: draft  
Version: ci-standards-v1

## Required Checks

Every pull request should run:

- config validation
- repository hygiene check
- Terraform format and validation when infra changes
- security baseline checks
- eval contract checks when prompts, policies, schemas, or data catalogs change

## Future Checks

When service code is added:

- Python lint
- Python type checks
- unit tests
- integration tests
- container build
- Helm template validation
- Kubernetes manifest validation

## Release Gate

Production promotion requires:

- passing security gates
- passing eval gates
- release metadata registered
- rollback path documented

