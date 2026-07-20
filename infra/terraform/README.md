# Terraform Infrastructure

This folder holds the cloud infrastructure for AegisRAG.

## Layout

```text
infra/terraform/
  envs/
    dev/
    staging/
    prod/
  modules/
    networking/
    kms/
    iam/
    s3-data-lake/
    dynamodb/
    aurora/
    elasticache/
    opensearch/
    sqs/
    eventbridge/
    eks/
    observability/
    bedrock-access/
  service-catalog/
```

## Build Order

1. providers and versions
2. remote state design
3. networking
4. KMS and IAM
5. data buckets
6. metadata stores
7. cache/search
8. EKS
9. queues/events
10. observability
11. model access

## Service Catalog

`infra/service-catalog/aegis-services.json` is the local deployment contract for
AegisRAG services. The Terraform dev environment loads it through the
`service-catalog` module so later EKS, Helm, IAM, and observability modules can
consume the same service metadata that compose and smoke tests validate.

## Current Status

The current files define a validated local service catalog and safe placeholders
for cloud resources. We will add real resources module by module.
