# ingestion-service

Turns approved source content into searchable/indexed knowledge.

Responsibilities:

- source collection
- security and PII scan
- parsing and normalization
- chunking
- metadata enrichment
- embedding generation
- index publishing
- release registry update

Rule:

- unapproved content must not enter production indexes.

## Local API Skeleton

Endpoints:

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/ingestion/synthetic-enterprise/run`

The local implementation reads the generated synthetic enterprise corpus,
publishes deterministic chunks to `data/processed/synthetic-enterprise`, and
writes a local hybrid index to `data/indexes/synthetic-enterprise`.

The local hybrid index includes:

- `keyword-index.json` for keyword postings
- `vector-index.json` for deterministic hash-vector embeddings
- `index-manifest.json` with chunk checksums, provider metadata, and index version
