# eval-service

Runs offline, CI, shadow, canary, and production evals.

Responsibilities:

- retrieval evals
- grounding evals
- license/permission evals
- PII leakage evals
- prompt injection evals
- latency and cost evals
- release gates

Hard failures:

- PII leakage
- cross-tenant leakage
- license violation
- permission violation
- successful prompt injection
