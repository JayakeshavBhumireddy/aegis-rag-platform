# Helm Charts

This folder contains reusable deployment charts for AegisRAG services.

## Charts

```text
infra/helm/aegis-service/
```

The `aegis-service` chart is a generic service chart. Each service gets its own values file.

## Values

Service-specific dev values are generated from:

```text
infra/service-catalog/aegis-services.json
```

Regenerate them with:

```bash
make helm-values
```

`make validate-infra` verifies the generated values stay aligned with the
service catalog and local compose runtime.

It also statically checks the reusable chart contract: stable app labels,
service-account wiring, env injection, health probes, resources, service port
mapping, and HPA target fields must remain present in the templates.
