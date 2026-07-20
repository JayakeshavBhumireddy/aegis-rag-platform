from __future__ import annotations

import json

from aegis_shared.contracts import RetrievalScope
from retrieval_service.index import publish_local_hybrid_index, search_local_hybrid_index
from retrieval_service.search import search_corpus


def test_search_filters_by_license_and_permission() -> None:
    scope = RetrievalScope(
        tenantId="tenant_123",
        modules=["Billing"],
        permissions=["Billing.View", "Billing.Submit"],
        productVersion="2026.2",
        trustLevel="approved",
    )

    results = search_corpus(query="monthly billing submission", retrieval_scope=scope)

    assert len(results) == 1
    assert results[0].metadata["module"] == "Billing"


def test_search_excludes_unpermitted_documents() -> None:
    scope = RetrievalScope(
        tenantId="tenant_123",
        modules=["Inventory"],
        permissions=["Inventory.View"],
        productVersion="2026.2",
        trustLevel="approved",
    )

    assert search_corpus(query="receive inventory", retrieval_scope=scope) == []


def test_hybrid_index_search_filters_by_scope(tmp_path) -> None:
    chunks = _chunks()
    publish_local_hybrid_index(chunks=chunks, index_dir=tmp_path)
    scope = RetrievalScope(
        tenantId="tenant_123",
        modules=["Billing"],
        permissions=["Billing.View", "Billing.Submit"],
        productVersion="2026.2",
        trustLevel="approved",
    )

    results = search_local_hybrid_index(
        query="monthly submission",
        retrieval_scope=scope,
        top_k=5,
        chunks=chunks,
        index_dir=tmp_path,
    )

    assert len(results) == 1
    assert results[0].metadata["retrievalMode"] == "local_hybrid"
    assert results[0].source_id == "doc_billing_monthly_submission"


def test_search_corpus_falls_back_when_index_missing() -> None:
    scope = RetrievalScope(
        tenantId="tenant_123",
        modules=["Billing"],
        permissions=["Billing.View", "Billing.Submit"],
        productVersion="2026.2",
        trustLevel="approved",
    )

    results = search_corpus(
        query="monthly submission",
        retrieval_scope=scope,
        documents=_chunks(),
    )

    assert len(results) == 1
    assert "retrievalMode" not in results[0].metadata


def test_search_corpus_can_rerank_candidates() -> None:
    scope = RetrievalScope(
        tenantId="tenant_123",
        modules=["Billing"],
        permissions=["Billing.View", "Billing.Submit"],
        productVersion="2026.2",
        trustLevel="approved",
    )

    results = search_corpus(
        query="billing submission",
        retrieval_scope=scope,
        top_k=1,
        retrieval_mode="hybrid_rerank",
        documents=[
            {
                "sourceId": "doc_billing_policy",
                "title": "Billing Policy",
                "body": "Billing policy notes.",
                "moduleId": "billing",
                "requiredLicense": "Billing",
                "requiredPermissions": ["Billing.View"],
                "trustLevel": "approved",
                "productVersion": "2026.2",
            },
            {
                "sourceId": "doc_billing_submission",
                "title": "Billing Submission",
                "body": "Submit monthly billing.",
                "moduleId": "billing",
                "requiredLicense": "Billing",
                "requiredPermissions": ["Billing.View"],
                "trustLevel": "approved",
                "productVersion": "2026.2",
            },
        ],
    )

    assert [result.source_id for result in results] == ["doc_billing_submission"]
    assert results[0].metadata["reranker"]["model"] == "local-lexical-reranker-v1"


def _chunks() -> list[dict]:
    return json.loads(
        """
        [
          {
            "chunkId": "doc_billing_monthly_submission#body",
            "sourceId": "doc_billing_monthly_submission",
            "title": "Monthly Submission Workflow",
            "text": "To open Monthly Submission, go to Billing > Monthly Submission.",
            "checksum": "billing-checksum",
            "metadata": {
              "module": "Billing",
              "moduleId": "billing",
              "requiredLicense": "Billing",
              "requiredPermissions": ["Billing.View", "Billing.Submit"],
              "trustLevel": "approved",
              "productVersion": "2026.2"
            }
          },
          {
            "chunkId": "doc_inventory_receiving#body",
            "sourceId": "doc_inventory_receiving",
            "title": "Receiving Workflow",
            "text": "To open Receiving, go to Inventory > Receiving.",
            "checksum": "inventory-checksum",
            "metadata": {
              "module": "Inventory",
              "moduleId": "inventory",
              "requiredLicense": "Inventory",
              "requiredPermissions": ["Inventory.View", "Inventory.Receive"],
              "trustLevel": "approved",
              "productVersion": "2026.2"
            }
          }
        ]
        """
    )
