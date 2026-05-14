# entitlement-service

Builds the entitlement envelope for each authenticated user.

Responsibilities:

- tenant resolution
- licensed modules
- enabled features
- product version
- user roles and permissions
- license and permission hash generation

Security:

- fail closed if an entitlement envelope cannot be created
- cache only short-lived envelopes

## Local API Skeleton

Endpoints:

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/entitlements/resolve`

Run locally:

```bash
PYTHONPATH=packages:services/entitlement-service/src \
  uv run uvicorn entitlement_service.main:app --reload
```

The first implementation uses an in-memory entitlement store for contract and
policy-flow development. Production resolution will replace this with source
backed tenant, user, role, license, and permission providers.
