# Local Tool Checklist V1

Install these tools before initializing Git and running local checks.

## Required

| Tool | Purpose |
|---|---|
| Git | version control |
| Python 3.12 | service code, scripts, evals |
| uv | Python package management |
| Docker Desktop | local dependencies |
| Terraform | infrastructure validation |
| Helm | Kubernetes chart validation |
| kubectl | Kubernetes interaction |
| AWS CLI | cloud access and identity checks |

## Recommended Install Order

1. Git
2. Python 3.12
3. uv
4. Docker Desktop
5. Terraform
6. Helm
7. kubectl
8. AWS CLI

## First Verification Commands

```bash
git --version
python --version
uv --version
docker --version
terraform version
helm version
kubectl version --client
aws --version
```

