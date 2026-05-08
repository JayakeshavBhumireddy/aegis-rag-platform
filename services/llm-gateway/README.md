# llm-gateway

Only service allowed to call foundation models.

Responsibilities:

- model/provider routing
- token budgets
- retries and timeouts
- circuit breakers
- provider fallback
- cost attribution
- prompt versioning

Supported providers should be abstracted behind a stable interface.
