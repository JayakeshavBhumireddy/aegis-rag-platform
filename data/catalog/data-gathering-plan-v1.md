# Data Gathering Plan V1

This plan defines how to gather data for the large-scale AI Assistant Platform showcase without using customer or tenant data.

## Data Safety Rules

1. Do not commit raw datasets to Git.
2. Do not ingest proprietary private product docs unless explicitly approved.
3. Do not use customer, personal, financial, regulated, credential, secret, or application-record data.
4. Record license and source URL for every dataset.
5. Run PII/security scans before indexing.
6. Version every raw, processed, chunked, embedded, and indexed artifact.

## Phase 0: Synthetic enterprise product-help Corpus

Purpose:

- prove entitlement checks
- prove navigation graph
- prove license and permission denials
- prove prompt/refusal behavior

Data to generate:

- modules
- licenses
- permissions
- routes
- workflows
- FAQs
- golden questions
- adversarial questions

Scale:

- 500-5,000 docs/routes/questions

## Phase 1: MS MARCO Small Subset

Purpose:

- local retrieval development
- first recall and MRR evals
- reranker testing

Data:

- 50k-100k passages
- dev queries
- qrels

Output artifacts:

- parsed passages
- chunks
- embeddings
- retrieval eval set

## Phase 2: MS MARCO 1M Performance Subset

Purpose:

- throughput testing
- index-size testing
- cache effectiveness testing
- p95/p99 latency measurement

Data:

- 1M passages
- representative query subset

## Phase 3: MS MARCO Full Corpus

Purpose:

- large-scale retrieval benchmark
- operational scale test
- index publishing workflow

Data:

- official passage ranking corpus
- queries
- relevance labels

## Phase 4: BEIR

Purpose:

- cross-domain retrieval robustness
- regression testing
- grounding and citation quality checks

Recommended subsets:

- SciFact
- FEVER
- HotpotQA
- NFCorpus

## Phase 5: Wikipedia Subset

Purpose:

- large general-knowledge indexing
- ingestion stress testing
- long-document chunking tests

Recommended start:

- selected topic subset
- then 1M article subset

## Storage Layout

```text
data/
  raw/
    msmarco/
    beir/
    wikipedia/
    synthetic-enterprise/
  processed/
    parsed/
    chunks/
    enriched/
    embeddings/
  indexes/
    opensearch/
    qdrant/
    navigation-graph/
  evals/
    golden/
    adversarial/
    regression/
    tenant-matrix/
```

## Source Approval Checklist

Before ingestion:

- source URL recorded
- license reviewed
- redistribution constraints reviewed
- PII risk assigned
- dataset owner assigned
- ingestion priority assigned
- expected storage size estimated
- eval purpose defined
