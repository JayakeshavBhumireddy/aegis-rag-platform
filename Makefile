SHELL := /bin/sh

.PHONY: help
help:
	@echo "AegisRAG project commands"
	@echo ""
	@echo "Local:"
	@echo "  make local-up          Start local dependencies"
	@echo "  make local-down        Stop local dependencies"
	@echo ""
	@echo "Terraform:"
	@echo "  make tf-fmt            Format Terraform files"
	@echo "  make tf-validate-dev   Validate dev Terraform"
	@echo ""
	@echo "Checks:"
	@echo "  make check             Run lightweight repository checks"
	@echo "  make validate-configs  Validate JSON and YAML config syntax"
	@echo "  make hygiene           Run repository hygiene checks"
	@echo "  make synthetic-data    Generate local synthetic corpus"

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
	python scripts/validation/validate_configs.py
	python scripts/validation/check_repo_hygiene.py

.PHONY: validate-configs
validate-configs:
	python scripts/validation/validate_configs.py

.PHONY: hygiene
hygiene:
	python scripts/validation/check_repo_hygiene.py

.PHONY: synthetic-data
synthetic-data:
	python scripts/data/generate_synthetic_corpus.py
