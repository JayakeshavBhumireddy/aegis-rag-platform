# Kubernetes Standards V1

Status: draft  
Version: kubernetes-standards-v1

## Namespaces

| Namespace | Purpose |
|---|---|
| aegis-system | platform components |
| aegis-apps | application services |

## Workload Requirements

Every service deployment must define:

- readiness probe
- liveness probe
- resource requests
- resource limits
- service account
- labels
- OpenTelemetry environment variables

## Security Requirements

- default deny network policy
- least-privilege service accounts
- no privileged containers by default
- secrets mounted through approved secret mechanisms
- images pinned by tag or digest

## Scaling

Stateless services should use HPA.

Model-serving workloads may use separate node pools and autoscaling rules.

