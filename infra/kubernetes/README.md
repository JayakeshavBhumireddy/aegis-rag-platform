# Kubernetes Infrastructure

This folder contains Kubernetes manifests that are not owned by a specific application service chart.

## Layout

```text
infra/kubernetes/
  namespaces/
  service-accounts/
  network-policies/
  observability/
  base/
```

Service deployments should generally use the reusable Helm chart in:

```text
infra/helm/aegis-service/
```

