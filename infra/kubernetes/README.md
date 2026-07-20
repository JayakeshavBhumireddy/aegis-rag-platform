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

## Network Policies

The default policy denies all ingress and egress in `aegis-apps`.
Catalog-derived allow policies are generated from:

```text
infra/service-catalog/aegis-services.json
```

Regenerate them with:

```bash
make k8s-policies
```

`make validate-infra` checks the generated policies exactly match the service
catalog.
