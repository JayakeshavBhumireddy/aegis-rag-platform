# Helm Standards V1

Status: draft  
Version: helm-standards-v1

## Chart Strategy

AegisRAG uses one reusable stateless service chart:

```text
infra/helm/aegis-service/
```

Each service provides values:

```text
infra/helm/values/{service}-{environment}.yaml
```

## Template Requirements

The reusable chart must support:

- deployment
- service
- HPA
- probes
- resources
- environment variables
- service account
- labels

## Rule

Service-specific behavior belongs in service code or values files, not copied Helm templates.

