# observability-service

Telemetry, audit, cost, and operational reporting.

Responsibilities:

- OpenTelemetry traces
- metrics and dashboards
- structured logs
- audit fanout
- cost ledger
- feedback aggregation
- incident evidence collection

Rule:

- redact PII from standard logs and store sensitive audit events separately.

## Local API Skeleton

Endpoints:

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/audit/records`
- `GET /v1/audit/records`
- `POST /v1/cost/events`
- `GET /v1/cost/events`
- `POST /v1/feedback/events`
- `GET /v1/feedback/events`

The service supports two local store modes:

- `memory` for fast unit tests and ephemeral development
- `sqlite` for restart-safe local audit, cost, and feedback event envelopes

Set these variables to use the SQLite event store:

```bash
export AEGIS_OBSERVABILITY_STORE_MODE=sqlite
export AEGIS_OBSERVABILITY_SQLITE_PATH=data/observability/observability-events.db
```

The local implementation is intended to validate event shape, assistant-api
audit behavior, and cost ledger semantics before replacing the sink with
durable cloud fanout.

Assistant audit events include deterministic local usage estimates for route,
latency, cost, provider, and token counts. These estimates support local release
gates before real provider billing data is available.

Assistant cost events are recorded once per answer with tenant, user, route,
usage, session ID, citation count, and confidence metadata. This keeps the
response usage block, audit trail, and cost ledger aligned for local validation.

Feedback events capture tenant, user, session, message, rating, comment,
category, and metadata fields. The local store is in memory, but it uses the
same event envelope as release, audit, and cost signals.
