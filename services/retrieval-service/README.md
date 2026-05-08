# retrieval-service

Performs scoped retrieval over approved content.

Responsibilities:

- build search filters from the policy scope
- hybrid keyword + vector retrieval
- metadata filtering
- source deduplication
- retrieval result packaging

Security:

- retrieve only content allowed by tenant, license, role, permission, state, product version, and trust level.
