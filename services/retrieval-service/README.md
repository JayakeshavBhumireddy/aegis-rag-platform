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

## Local Hybrid Retrieval

The local implementation reads processed chunks and prefers the generated local
hybrid index when available:

- keyword postings simulate the OpenSearch path
- deterministic hash vectors simulate the Qdrant/vector path
- metadata filters enforce license, permission, product version, and trust level
- direct chunk scanning remains as a deterministic fallback when index artifacts
  are missing
- `retrievalMode=hybrid_rerank` runs candidates through the local lexical
  reranker and adds explainable `metadata.reranker` signals
