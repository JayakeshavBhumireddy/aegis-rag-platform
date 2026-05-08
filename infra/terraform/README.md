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

## Current Status

The current files are safe placeholders. We will add real resources module by module.
