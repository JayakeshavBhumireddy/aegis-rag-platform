SHELL := /bin/sh
PYTHON ?= python3

.PHONY: help
help:
	@echo "AegisRAG project commands"
	@echo ""
	@echo "Local:"
	@echo "  make local-up          Start local service stack"
	@echo "  make local-down        Stop local service stack"
	@echo ""
	@echo "Terraform:"
	@echo "  make tf-fmt            Format Terraform files"
	@echo "  make tf-validate-dev   Validate dev Terraform"
	@echo ""
	@echo "Checks:"
	@echo "  make check             Run lightweight repository checks"
	@echo "  make validate-configs  Validate JSON and YAML config syntax"
	@echo "  make hygiene           Run repository hygiene checks"
	@echo "  make validate-infra    Validate infra service catalog contracts"
	@echo "  make validate-api      Validate implemented API surface"
	@echo "  make helm-values       Generate Helm values from service catalog"
	@echo "  make k8s-policies      Generate Kubernetes policies from service catalog"
	@echo "  make synthetic-data    Generate local synthetic corpus"
	@echo "  make release-gate      Run local release gate"
	@echo "  make release-candidate Write local candidate release metadata"
	@echo "  make release-promote   Promote local candidate to active release"
	@echo "  make release-rollback  Roll back to the previous local active release"
	@echo "  make stack-check       Check running local service health endpoints"
	@echo "  make http-smoke        Start local FastAPI processes and run HTTP smoke test"

.PHONY: local-up
local-up:
	docker compose up -d

.PHONY: local-down
local-down:
	docker compose down

.PHONY: tf-fmt
tf-fmt:
	terraform -chdir=infra/terraform fmt -recursive

.PHONY: tf-validate-dev
tf-validate-dev:
	terraform -chdir=infra/terraform/envs/dev init -backend=false
	terraform -chdir=infra/terraform/envs/dev validate

.PHONY: check
check:
	$(PYTHON) scripts/validation/validate_configs.py
	$(PYTHON) scripts/validation/check_repo_hygiene.py

.PHONY: validate-configs
validate-configs:
	$(PYTHON) scripts/validation/validate_configs.py

.PHONY: hygiene
hygiene:
	$(PYTHON) scripts/validation/check_repo_hygiene.py

.PHONY: validate-infra
validate-infra:
	$(PYTHON) scripts/validation/validate_infra_contracts.py

.PHONY: validate-api
validate-api:
	uv run python scripts/validation/validate_api_contracts.py

.PHONY: helm-values
helm-values:
	uv run python scripts/infra/generate_helm_values.py

.PHONY: k8s-policies
k8s-policies:
	uv run python scripts/infra/generate_kubernetes_network_policies.py

.PHONY: synthetic-data
synthetic-data:
	$(PYTHON) scripts/data/generate_synthetic_corpus.py

.PHONY: release-gate
release-gate:
	$(PYTHON) scripts/validation/run_release_gate.py

.PHONY: release-candidate
release-candidate:
	uv run python scripts/release/local_release.py candidate

.PHONY: release-promote
release-promote:
	uv run python scripts/release/local_release.py promote

.PHONY: release-rollback
release-rollback:
	uv run python scripts/release/local_release.py rollback

.PHONY: stack-check
stack-check:
	$(PYTHON) scripts/validation/check_local_stack.py

.PHONY: http-smoke
http-smoke:
	uv run python scripts/validation/run_http_smoke.py
