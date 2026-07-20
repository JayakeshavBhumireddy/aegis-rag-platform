from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from retrieval_service.index import publish_local_hybrid_index

ROOT = Path(__file__).resolve().parents[4]
RAW_DIR = ROOT / "data" / "raw" / "synthetic-enterprise"
PROCESSED_DIR = ROOT / "data" / "processed" / "synthetic-enterprise"
INDEX_DIR = ROOT / "data" / "indexes" / "synthetic-enterprise"


def run_synthetic_ingestion(
    *,
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    index_dir: Path = INDEX_DIR,
) -> dict[str, Any]:
    documents = _read_json(raw_dir / "documents.json")
    chunks = [_chunk_document(document) for document in documents]

    _write_json(processed_dir / "chunks.json", chunks)
    manifest = publish_local_hybrid_index(chunks=chunks, index_dir=index_dir)

    return {
        "status": "ok",
        "documents": len(documents),
        "chunks": len(chunks),
        "processedPath": str(processed_dir / "chunks.json"),
        "indexManifestPath": str(index_dir / "index-manifest.json"),
        "indexVersion": manifest["indexVersion"],
        "indexType": manifest["indexType"],
    }


def _chunk_document(document: dict[str, Any]) -> dict[str, Any]:
    text = str(document["body"])
    chunk_id = f"{document['sourceId']}#body"
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "chunkId": chunk_id,
        "sourceId": document["sourceId"],
        "title": document["title"],
        "text": text,
        "checksum": checksum,
        "metadata": {
            "module": document["requiredLicense"],
            "moduleId": document["moduleId"],
            "requiredLicense": document["requiredLicense"],
            "requiredPermissions": document["requiredPermissions"],
            "trustLevel": document["trustLevel"],
            "productVersion": document["productVersion"],
        },
    }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    result = run_synthetic_ingestion()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
