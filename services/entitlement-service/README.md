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

## Metadata Store Mode

For local production-shaped testing, the service can resolve entitlements from
the platform metadata tables:

```bash
export AEGIS_ENTITLEMENT_STORE_MODE=metadata
export AEGIS_ENTITLEMENT_SQLITE_PATH=/path/to/platform-metadata.db
```

The metadata-backed resolver reads active tenants, users, tenant memberships,
roles, active licenses, and role permissions. It fails closed when any required
scope element is missing or disabled.
