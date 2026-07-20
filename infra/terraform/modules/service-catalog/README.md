# service-catalog module

Purpose:

- expose the versioned AegisRAG service catalog to Terraform environments
- keep service app names, ports, health paths, and dependency metadata aligned
- provide a stable input for later EKS, Helm, IAM, and observability modules

The catalog is intentionally data-only. It does not create cloud resources by
itself; downstream modules consume its outputs.
