# eval-service

Runs offline, CI, shadow, canary, and production evals.

Responsibilities:

- retrieval evals
- grounding evals
- license/permission evals
- PII leakage evals
- prompt injection evals
- latency and cost evals
- feedback mining into reviewable eval candidates
- release gates

Hard failures:

- PII leakage
- cross-tenant leakage
- license violation
- permission violation
- successful prompt injection

Endpoints:

- `POST /v1/evals/synthetic-enterprise/run`
- `POST /v1/evals/feedback/mine`
- `POST /v1/releases/local/candidate`
- `POST /v1/releases/local/promote`
- `POST /v1/releases/local/rollback`
