from __future__ import annotations

from fastapi import FastAPI

from ingestion_service.pipeline import run_synthetic_ingestion

SERVICE_VERSION = "ingestion-service-v0"

app = FastAPI(title="AegisRAG ingestion-service", version=SERVICE_VERSION)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/ingestion/synthetic-enterprise/run")
def run() -> dict:
    return run_synthetic_ingestion()
