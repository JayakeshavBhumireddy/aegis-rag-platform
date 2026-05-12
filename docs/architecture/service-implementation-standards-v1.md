# Service Implementation Standards V1

Status: draft  
Version: service-implementation-standards-v1

This document defines implementation standards for AegisRAG services.

## Service Requirements

Every service must provide:

- `/health/live`
- `/health/ready`
- structured logs
- OpenTelemetry trace propagation
- request ID propagation
- config loaded from environment variables
- no direct foundation model calls unless it is `llm-gateway`

## API Requirements

Every API response must include or propagate:

- request ID
- trace ID
- service version
- error code when failing

## Security Requirements

Security-critical services must fail closed:

- entitlement-service
- policy-service
- verification-service for high-risk flows
- PII scanning for sensitive flows

## Python Service Baseline

Recommended framework:

- FastAPI
- Pydantic
- httpx
- structlog or standard structured logging
- OpenTelemetry SDK

Recommended package manager:

- uv

## Configuration

Configuration comes from:

1. environment variables
2. mounted config files
3. secret manager references

Do not hardcode:

- secrets
- tenant IDs
- provider credentials
- model names for production routes

