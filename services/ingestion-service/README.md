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
