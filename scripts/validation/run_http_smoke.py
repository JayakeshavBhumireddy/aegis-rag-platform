"""Start local FastAPI services and run an authenticated assistant smoke test."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHONPATH_ENTRIES = [
    "packages",
    "services/auth-service/src",
    "services/entitlement-service/src",
    "services/ingestion-service/src",
    "services/observability-service/src",
    "services/policy-service/src",
    "services/retrieval-service/src",
    "services/reranker-service/src",
    "services/llm-gateway/src",
    "services/verification-service/src",
    "services/context-service/src",
    "services/assistant-api/src",
    "services/eval-service/src",
]
OBSERVABILITY_SMOKE_DB = ROOT / "data" / "processed" / "observability-smoke.db"
RELEASE_SMOKE_DIR = ROOT / "data" / "processed" / "release-smoke"
RELEASE_SMOKE_CANDIDATE = RELEASE_SMOKE_DIR / "local-candidate.json"
RELEASE_SMOKE_ACTIVE = RELEASE_SMOKE_DIR / "local-active.json"
RELEASE_SMOKE_ROLLBACK = RELEASE_SMOKE_DIR / "local-rollback.json"


@dataclass(frozen=True)
class ServiceProcess:
    name: str
    app: str
    port: int
    env: dict[str, str] | None = None


SERVICES = [
    ServiceProcess("auth-service", "auth_service.main:app", 8010),
    ServiceProcess("entitlement-service", "entitlement_service.main:app", 8011),
    ServiceProcess("policy-service", "policy_service.main:app", 8012),
    ServiceProcess("context-service", "context_service.main:app", 8013),
    ServiceProcess("retrieval-service", "retrieval_service.main:app", 8014),
    ServiceProcess("llm-gateway", "llm_gateway.main:app", 8015),
    ServiceProcess("verification-service", "verification_service.main:app", 8016),
    ServiceProcess(
        "observability-service",
        "observability_service.main:app",
        8017,
        env={
            "AEGIS_OBSERVABILITY_STORE_MODE": "sqlite",
            "AEGIS_OBSERVABILITY_SQLITE_PATH": str(OBSERVABILITY_SMOKE_DB),
        },
    ),
    ServiceProcess("ingestion-service", "ingestion_service.main:app", 8018),
    ServiceProcess("eval-service", "eval_service.main:app", 8019),
    ServiceProcess(
        "assistant-api",
        "assistant_api.main:app",
        8000,
        env={
            "AEGIS_ASSISTANT_DEPENDENCY_MODE": "http",
            "AEGIS_ENTITLEMENT_URL": "http://localhost:8011",
            "AEGIS_POLICY_URL": "http://localhost:8012",
            "AEGIS_CONTEXT_URL": "http://localhost:8013",
            "AEGIS_RETRIEVAL_URL": "http://localhost:8014",
            "AEGIS_LLM_GATEWAY_URL": "http://localhost:8015",
            "AEGIS_VERIFICATION_URL": "http://localhost:8016",
            "AEGIS_OBSERVABILITY_URL": "http://localhost:8017",
            "AEGIS_ACTIVE_RELEASE_PATH": str(RELEASE_SMOKE_ACTIVE),
        },
    ),
]


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(ROOT / entry) for entry in PYTHONPATH_ENTRIES)
    env.setdefault("UV_CACHE_DIR", str(ROOT / ".uv-cache"))
    env.setdefault("AEGIS_AUTH_DEV_SECRET", "aegis-local-dev-secret")

    processes: list[subprocess.Popen] = []
    try:
        _run([sys.executable, "scripts/data/generate_synthetic_corpus.py"], env)
        _run([sys.executable, "-m", "ingestion_service.pipeline"], env)
        if OBSERVABILITY_SMOKE_DB.exists():
            OBSERVABILITY_SMOKE_DB.unlink()
        for release_path in (RELEASE_SMOKE_CANDIDATE, RELEASE_SMOKE_ACTIVE, RELEASE_SMOKE_ROLLBACK):
            if release_path.exists():
                release_path.unlink()
        _prepare_smoke_release(env)

        for service in SERVICES:
            service_env = env.copy()
            service_env.update(service.env or {})
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    service.app,
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(service.port),
                    "--log-level",
                    "warning",
                ],
                cwd=ROOT,
                env=service_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            processes.append(process)

        for service, process in zip(SERVICES, processes, strict=True):
            _wait_for_health(service.name, service.port, process)

        token = _create_token(env)
        response = _post_json(
            "http://localhost:8000/v1/assistant/messages",
            {
                "message": "Where do I submit monthly billing?",
                "tenantId": "tenant_123",
                "userId": "user_123",
                "sessionId": "session_smoke",
                "uiContext": {"module": "Billing", "page": "Monthly Submission"},
            },
            headers={"authorization": f"Bearer {token}"},
        )
        if response.get("route") != "scoped_rag_http":
            print(f"Unexpected assistant route: {response}")
            return 1
        if "Billing > Monthly Submission" not in response.get("answer", ""):
            print(f"Unexpected assistant answer: {response}")
            return 1
        release_metadata = response.get("releaseMetadata", {})
        if release_metadata.get("releaseId") != _read_smoke_release_id():
            print(f"Assistant did not use smoke active release: {response}")
            return 1
        if release_metadata.get("status") != "prod":
            print(f"Assistant active release was not promoted: {response}")
            return 1
        audit_events = _get_json("http://localhost:8017/v1/audit/records")
        cost_events = _get_json("http://localhost:8017/v1/cost/events")
        if not any(
            event.get("payload", {}).get("stage") == "response_completed"
            for event in audit_events
        ):
            print(f"Missing response_completed audit event: {audit_events}")
            return 1
        if not any(
            event.get("payload", {}).get("route") == "scoped_rag_http"
            for event in cost_events
        ):
            print(f"Missing scoped_rag_http cost event: {cost_events}")
            return 1
        if not any(
            event.get("payload", {})
            .get("metadata", {})
            .get("releaseMetadata", {})
            .get("releaseId")
            == _read_smoke_release_id()
            for event in cost_events
        ):
            print(f"Missing smoke release metadata in cost events: {cost_events}")
            return 1

        print("HTTP smoke test passed.")
        return 0
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def _run(command: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _prepare_smoke_release(env: dict[str, str]) -> None:
    command = [
        sys.executable,
        "-c",
        (
            "from pathlib import Path; "
            "from eval_service.release_registry import "
            "promote_local_release_candidate, write_local_release_candidate; "
            f"candidate=Path({str(RELEASE_SMOKE_CANDIDATE)!r}); "
            f"active=Path({str(RELEASE_SMOKE_ACTIVE)!r}); "
            f"rollback=Path({str(RELEASE_SMOKE_ROLLBACK)!r}); "
            "write_local_release_candidate(output_path=candidate); "
            "promote_local_release_candidate("
            "candidate_path=candidate, active_path=active, previous_active_path=rollback)"
        ),
    ]
    _run(command, env)


def _read_smoke_release_id() -> str:
    release = json.loads(RELEASE_SMOKE_ACTIVE.read_text(encoding="utf-8"))
    return str(release["releaseId"])


def _wait_for_health(name: str, port: int, process: subprocess.Popen) -> None:
    url = f"http://localhost:{port}/health/ready"
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = _read_process_output(process)
            raise RuntimeError(
                f"{name} exited with code {process.returncode} before becoming healthy.\n"
                f"{output}"
            )
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                body = json.loads(response.read().decode("utf-8"))
            if body.get("status") == "ok":
                return
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(0.25)
    raise RuntimeError(f"{name} did not become healthy on {url}; process is still running")


def _read_process_output(process: subprocess.Popen) -> str:
    try:
        output, _ = process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        return ""
    return output or ""


def _create_token(env: dict[str, str]) -> str:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from auth_service.local_tokens import create_local_dev_token; "
                "print(create_local_dev_token(tenant_id='tenant_123', user_id='user_123'))"
            ),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def _post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"content-type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(url: str) -> list[dict]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
