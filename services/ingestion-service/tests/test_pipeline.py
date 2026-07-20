from __future__ import annotations

import json

from ingestion_service.pipeline import run_synthetic_ingestion


def test_synthetic_ingestion_writes_chunks_and_manifest(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    index_dir = tmp_path / "indexes"
    raw_dir.mkdir()
    (raw_dir / "documents.json").write_text(
        json.dumps(
            [
                {
                    "sourceId": "doc_billing_monthly_submission",
                    "title": "Monthly Submission Workflow",
                    "moduleId": "billing",
                    "requiredLicense": "Billing",
                    "requiredPermissions": ["Billing.View", "Billing.Submit"],
                    "trustLevel": "approved",
                    "productVersion": "2026.2",
                    "body": "To open Monthly Submission, go to Billing > Monthly Submission.",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_synthetic_ingestion(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        index_dir=index_dir,
    )

    chunks = json.loads((processed_dir / "chunks.json").read_text(encoding="utf-8"))
    manifest = json.loads((index_dir / "index-manifest.json").read_text(encoding="utf-8"))
    keyword_index = json.loads((index_dir / "keyword-index.json").read_text(encoding="utf-8"))
    vector_index = json.loads((index_dir / "vector-index.json").read_text(encoding="utf-8"))

    assert result["status"] == "ok"
    assert result["indexType"] == "local_hybrid"
    assert chunks[0]["chunkId"] == "doc_billing_monthly_submission#body"
    assert manifest["indexType"] == "local_hybrid"
    assert manifest["chunkCount"] == 1
    assert manifest["chunks"][0]["metadata"]["module"] == "Billing"
    assert "billing" in keyword_index["postings"]
    assert "doc_billing_monthly_submission#body" in vector_index["vectors"]
