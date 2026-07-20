from __future__ import annotations

from aegis_shared.contracts import EventEnvelope
from fastapi import FastAPI
from pydantic import BaseModel

from eval_service.feedback_mining import mine_feedback_eval_candidates
from eval_service.release_registry import (
    promote_local_release_candidate,
    rollback_local_release,
    write_local_release_candidate,
)
from eval_service.runner import run_synthetic_eval

SERVICE_VERSION = "eval-service-v0"

app = FastAPI(title="AegisRAG eval-service", version=SERVICE_VERSION)


class FeedbackMiningRequest(BaseModel):
    events: list[EventEnvelope]


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/evals/synthetic-enterprise/run")
def run() -> dict:
    return run_synthetic_eval()


@app.post("/v1/evals/feedback/mine")
def mine_feedback(request: FeedbackMiningRequest) -> dict:
    return mine_feedback_eval_candidates(request.events)


@app.post("/v1/releases/local/candidate")
def write_candidate() -> dict:
    return write_local_release_candidate()


@app.post("/v1/releases/local/promote")
def promote_candidate() -> dict:
    return promote_local_release_candidate()


@app.post("/v1/releases/local/rollback")
def rollback_release() -> dict:
    return rollback_local_release()
