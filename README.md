# AegisRAG Platform

Status: initial project scaffold  
Date: 2026-05-07

This project contains the enterprise-scale architecture, service boundaries, data catalog, configs, infra placeholders, and evaluation structure for AegisRAG, a tenant-aware enterprise RAG platform.

The goal is to build a production-grade AI platform, not a simple RAG demo. The platform is designed for:

- multi-tenant isolation
- license and permission scoped retrieval
- high throughput and low latency
- deterministic security controls
- safe context, memory, and state
- model/provider abstraction
- continuous evals and release gates
- fallback and degraded-mode operation

## Folder Structure

```text
aegis-rag-platform/
  docs/
    architecture/     system architecture and service designs
    decisions/        architecture decision records
    security/         threat model, leakage controls, policy model
    operations/       runbooks, SLOs, deployment modes
    evals/            eval strategy and release gates
  data/
    catalog/          dataset manifests and governance metadata
    raw/              local raw dataset landing area
    processed/        parsed/chunked/enriched data
    indexes/          generated index artifacts or index manifests
    evals/            golden, adversarial, regression eval datasets
  configs/
    environments/     dev/stage/prod configs
    policies/         policy and entitlement rules
    prompts/          versioned prompt templates
    routing/          inference route configs
  services/
    assistant-api/
    entitlement-service/
    policy-service/
    context-service/
    retrieval-service/
    reranker-service/
    llm-gateway/
    verification-service/
    ingestion-service/
    eval-service/
    observability-service/
  infra/
    terraform/
    kubernetes/
    helm/
  scripts/
  tests/
```

## Initial Dataset Strategy

Use public datasets first. Do not use customer or tenant data for the showcase.

Recommended sequence:

1. MS MARCO passage ranking subset for local retrieval/eval development.
2. MS MARCO full passage corpus for large-scale retrieval benchmarking.
3. BEIR datasets for cross-domain retrieval quality.
4. Wikipedia subset for large general knowledge indexing.
5. Synthetic enterprise product/help-navigation content for entitlement and policy simulation.

Large datasets should be downloaded into controlled storage, not committed to source control.

## Service Spine

```text
Edge Security
-> API Gateway
-> Auth
-> Tenant Resolver
-> Entitlement Service
-> Policy Engine
-> Intent/Risk/PII Classification
-> Inference Router
-> Cache / Navigation Graph / FAQ / Scoped RAG
-> LLM Gateway
-> Answer Verification
-> Output Guardrails
-> Audit + Cost + Evals + Feedback
```

## Recommended Enterprise Stack

- AWS CloudFront, WAF, Shield
- EKS
- Amazon Verified Permissions / Cedar
- Aurora PostgreSQL and DynamoDB
- ElastiCache for Valkey
- OpenSearch Serverless
- S3
- EventBridge and SQS
- SageMaker or NVIDIA Triton for ONNX/TensorRT serving
- Bedrock through an LLM Gateway, with provider fallback
- Bedrock Guardrails plus deterministic verification
- OpenTelemetry, CloudWatch, Datadog/Grafana
- Terraform and Argo CD

## Next Steps

1. Finalize service contracts.
2. Add dataset download manifests and ingestion jobs.
3. Define eval schemas.
4. Create Terraform module skeletons.
5. Add API skeletons for core services.
