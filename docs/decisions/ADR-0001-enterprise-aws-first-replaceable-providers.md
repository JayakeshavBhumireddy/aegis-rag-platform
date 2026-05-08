# ADR-0001: AWS-First Enterprise Stack With Replaceable Providers

Date: 2026-05-07  
Status: proposed

## Context

The platform must support high throughput, low latency, multi-tenant isolation, strict authorization, auditable behavior, and safe model inference. We need enterprise-grade managed services while avoiding permanent lock-in at the application layer.

## Decision

Use AWS as the default enterprise deployment platform:

- CloudFront, WAF, Shield
- EKS
- Amazon Verified Permissions / Cedar
- Aurora PostgreSQL, DynamoDB
- ElastiCache for Valkey
- OpenSearch Serverless
- S3
- EventBridge and SQS
- SageMaker or NVIDIA Triton on EKS
- Bedrock through an LLM Gateway
- Bedrock Guardrails plus custom deterministic verification
- OpenTelemetry and CloudWatch

Keep provider interfaces replaceable:

- PolicyProvider
- SearchProvider
- CacheProvider
- EmbeddingProvider
- RerankerProvider
- LLMProvider
- GuardrailProvider
- AuditProvider

## Consequences

Positive:

- Strong enterprise security and operations baseline.
- Managed services reduce operational burden.
- Provider abstraction allows benchmarking and later replacement.

Tradeoffs:

- More upfront architecture work.
- EKS and multi-service operations require mature DevOps practices.
- Provider abstraction must be carefully designed to avoid lowest-common-denominator APIs.
