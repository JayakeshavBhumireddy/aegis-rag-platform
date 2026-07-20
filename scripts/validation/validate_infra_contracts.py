"""Validate infrastructure service catalog contracts against local runtime files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SERVICE_CATALOG_PATH = ROOT / "infra" / "service-catalog" / "aegis-services.json"
COMPOSE_FILE = ROOT / "docker-compose.yml"
DEV_TERRAFORM_MAIN = ROOT / "infra" / "terraform" / "envs" / "dev" / "main.tf"
HELM_VALUES_DIR = ROOT / "infra" / "helm" / "values"
HELM_CHART_DIR = ROOT / "infra" / "helm" / "aegis-service"
NETWORK_POLICY_PATH = (
    ROOT / "infra" / "kubernetes" / "network-policies" / "catalog-service-traffic.yaml"
)
sys.path.insert(0, str(ROOT))
from scripts.infra.generate_helm_values import render_values  # noqa: E402
from scripts.infra.generate_kubernetes_network_policies import render_network_policies  # noqa: E402

EXPECTED_PLATFORM_SERVICES = {
    "assistant-api",
    "auth-service",
    "context-service",
    "entitlement-service",
    "eval-service",
    "ingestion-service",
    "llm-gateway",
    "observability-service",
    "policy-service",
    "retrieval-service",
    "reranker-service",
    "verification-service",
}
SERVICE_URL_ENV = {
    "entitlement-service": "AEGIS_ENTITLEMENT_URL",
    "policy-service": "AEGIS_POLICY_URL",
    "context-service": "AEGIS_CONTEXT_URL",
    "retrieval-service": "AEGIS_RETRIEVAL_URL",
    "llm-gateway": "AEGIS_LLM_GATEWAY_URL",
    "verification-service": "AEGIS_VERIFICATION_URL",
    "observability-service": "AEGIS_OBSERVABILITY_URL",
}


def main() -> int:
    errors: list[str] = []
    catalog = _load_catalog()
    services = catalog.get("services", {})
    if not isinstance(services, dict):
        errors.append("service catalog must contain a services object")
        services = {}

    service_names = set(services)
    missing = sorted(EXPECTED_PLATFORM_SERVICES - service_names)
    extra = sorted(service_names - EXPECTED_PLATFORM_SERVICES)
    if missing:
        errors.append(f"service catalog missing services: {missing}")
    if extra:
        errors.append(f"service catalog contains unexpected services: {extra}")

    compose_services = _parse_compose_services(COMPOSE_FILE.read_text(encoding="utf-8"))
    for name, service in sorted(services.items()):
        errors.extend(_validate_catalog_service(name, service))
        errors.extend(_validate_helm_values(name, service))
        compose = compose_services.get(name)
        if compose is None:
            errors.append(f"docker-compose.yml missing service from catalog: {name}")
            continue
        if compose.get("app") != service.get("app"):
            errors.append(
                f"{name}: compose app {compose.get('app')!r} does not match catalog "
                f"{service.get('app')!r}"
            )
        if compose.get("port") != service.get("port"):
            errors.append(
                f"{name}: compose port {compose.get('port')!r} does not match catalog "
                f"{service.get('port')!r}"
            )

    assistant = services.get("assistant-api", {})
    dependencies = set(assistant.get("dependencies", []))
    expected_dependencies = EXPECTED_PLATFORM_SERVICES - {
        "assistant-api",
        "auth-service",
        "eval-service",
        "ingestion-service",
        "reranker-service",
    }
    if dependencies != expected_dependencies:
        errors.append(
            "assistant-api dependencies do not match expected runtime dependencies: "
            f"{sorted(dependencies)}"
        )
    errors.extend(_validate_helm_chart_contract())
    errors.extend(_validate_network_policies(services))

    terraform_text = DEV_TERRAFORM_MAIN.read_text(encoding="utf-8")
    if "service-catalog/aegis-services.json" not in terraform_text:
        errors.append("dev Terraform does not load infra/service-catalog/aegis-services.json")
    if 'source  = "../../modules/service-catalog"' not in terraform_text:
        errors.append("dev Terraform does not instantiate the service-catalog module")

    if errors:
        print("Infrastructure contract validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Infrastructure contract validation passed.")
    return 0


def _load_catalog() -> dict[str, Any]:
    return json.loads(SERVICE_CATALOG_PATH.read_text(encoding="utf-8"))


def _validate_catalog_service(name: str, service: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(service, dict):
        return [f"{name}: service catalog entry must be an object"]
    for field in ("app", "port", "healthReadyPath", "healthLivePath", "dependencies", "env"):
        if field not in service:
            errors.append(f"{name}: missing required catalog field {field}")
    if not isinstance(service.get("app"), str) or not service.get("app", "").endswith(":app"):
        errors.append(f"{name}: app must be an ASGI app import ending in :app")
    if not isinstance(service.get("port"), int):
        errors.append(f"{name}: port must be an integer")
    if service.get("healthReadyPath") != "/health/ready":
        errors.append(f"{name}: healthReadyPath must be /health/ready")
    if service.get("healthLivePath") != "/health/live":
        errors.append(f"{name}: healthLivePath must be /health/live")
    if not isinstance(service.get("dependencies"), list):
        errors.append(f"{name}: dependencies must be a list")
    if not isinstance(service.get("env"), dict):
        errors.append(f"{name}: env must be an object")
    return errors


def _validate_helm_values(name: str, service: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    path = HELM_VALUES_DIR / f"{name}-dev.yaml"
    if not path.exists():
        return [f"missing Helm values file for service catalog entry: {path}"]
    text = path.read_text(encoding="utf-8")
    expected_text = render_values(name, service)
    if text != expected_text:
        errors.append(f"{path}: generated Helm values are out of date")
    expected_snippets = [
        f"nameOverride: {name}",
        f"repository: example/{name}",
        "targetPort: 8000",
        f"    value: {json.dumps(service['app'])}",
        f"  path: {service['healthReadyPath']}",
        f"  path: {service['healthLivePath']}",
    ]
    for snippet in expected_snippets:
        if snippet not in text:
            errors.append(f"{path}: missing expected snippet {snippet!r}")
    if name == "assistant-api":
        for dependency, env_name in SERVICE_URL_ENV.items():
            expected = f"    value: \"http://{dependency}:8000\""
            if env_name not in text or expected not in text:
                errors.append(f"{path}: missing assistant dependency env {env_name}")
    return errors


def _validate_network_policies(services: dict[str, Any]) -> list[str]:
    if not NETWORK_POLICY_PATH.exists():
        return [f"missing Kubernetes network policy file: {NETWORK_POLICY_PATH}"]
    text = NETWORK_POLICY_PATH.read_text(encoding="utf-8")
    expected = render_network_policies(services)
    errors: list[str] = []
    if text != expected:
        errors.append(f"{NETWORK_POLICY_PATH}: generated network policies are out of date")
    for dependency in services["assistant-api"]["dependencies"]:
        snippets = [
            f"app.kubernetes.io/name: {dependency}",
            f"name: allow-{dependency}-ingress-from-assistant",
        ]
        for snippet in snippets:
            if snippet not in text:
                errors.append(f"{NETWORK_POLICY_PATH}: missing expected snippet {snippet!r}")
    return errors


def _validate_helm_chart_contract() -> list[str]:
    errors: list[str] = []
    files = {
        "deployment": HELM_CHART_DIR / "templates" / "deployment.yaml",
        "service": HELM_CHART_DIR / "templates" / "service.yaml",
        "hpa": HELM_CHART_DIR / "templates" / "hpa.yaml",
        "values": HELM_CHART_DIR / "values.yaml",
    }
    for name, path in files.items():
        if not path.exists():
            errors.append(f"missing Helm chart file: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in _required_helm_snippets(name):
            if snippet not in text:
                errors.append(f"{path}: missing required chart snippet {snippet!r}")
    return errors


def _required_helm_snippets(file_key: str) -> list[str]:
    snippets = {
        "deployment": [
            "app.kubernetes.io/name: {{ include \"aegis-service.name\" . }}",
            "app.kubernetes.io/part-of: aegis-rag",
            "serviceAccountName: {{ .Values.serviceAccount.name }}",
            "image: \"{{ .Values.image.repository }}:{{ .Values.image.tag }}\"",
            "containerPort: {{ .Values.service.targetPort }}",
            "{{- toYaml .Values.env | nindent 12 }}",
            "readinessProbe:",
            "path: {{ .Values.readinessProbe.path }}",
            "livenessProbe:",
            "path: {{ .Values.livenessProbe.path }}",
            "{{- toYaml .Values.resources | nindent 12 }}",
        ],
        "service": [
            "kind: Service",
            "port: {{ .Values.service.port }}",
            "targetPort: http",
            "app.kubernetes.io/name: {{ include \"aegis-service.name\" . }}",
        ],
        "hpa": [
            "{{- if .Values.autoscaling.enabled }}",
            "kind: HorizontalPodAutoscaler",
            "kind: Deployment",
            "minReplicas: {{ .Values.autoscaling.minReplicas }}",
            "maxReplicas: {{ .Values.autoscaling.maxReplicas }}",
            "averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}",
        ],
        "values": [
            "replicaCount: 2",
            "serviceAccount:",
            "resources:",
            "readinessProbe:",
            "livenessProbe:",
            "autoscaling:",
        ],
    }
    return snippets[file_key]


def _parse_compose_services(compose_text: str) -> dict[str, dict[str, Any]]:
    services: dict[str, dict[str, Any]] = {}
    current: str | None = None
    in_services = False
    for line in compose_text.splitlines():
        if line == "services:":
            in_services = True
            continue
        if not in_services:
            continue
        service_match = re.match(r"^  ([a-z0-9-]+):$", line)
        if service_match:
            current = service_match.group(1)
            services.setdefault(current, {})
            continue
        if current is None:
            continue
        app_match = re.match(r"^      AEGIS_SERVICE_APP: ([A-Za-z0-9_.:]+)$", line)
        if app_match:
            services[current]["app"] = app_match.group(1)
            continue
        port_match = re.match(r'^      - "([0-9]+):8000"$', line)
        if port_match:
            services[current]["port"] = int(port_match.group(1))
    return services


if __name__ == "__main__":
    sys.exit(main())
