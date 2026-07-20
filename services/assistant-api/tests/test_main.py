from __future__ import annotations

from assistant_api.cache import GLOBAL_EXACT_CACHE
from assistant_api.main import app
from auth_service.local_tokens import create_local_dev_token
from fastapi.testclient import TestClient


def test_messages_endpoint_returns_navigation_answer() -> None:
    GLOBAL_EXACT_CACHE.clear()
    client = TestClient(app)

    response = client.post(
        "/v1/assistant/messages",
        headers={"Authorization": f"Bearer {_token()}"},
        json={
            "message": "Where do I submit monthly billing?",
            "tenantId": "tenant_123",
            "userId": "user_123",
            "sessionId": "session_123",
            "uiContext": {"module": "Billing", "page": "Monthly Submission"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "navigation_graph"
    assert body["citations"]
    assert body["usage"]["estimatedCostUsd"] <= 0.001


def test_messages_endpoint_fails_closed_for_unknown_user() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/assistant/messages",
        headers={
            "Authorization": (
                f"Bearer {_token(tenant_id='tenant_missing', user_id='user_missing')}"
            )
        },
        json={
            "message": "Where do I submit monthly billing?",
            "tenantId": "tenant_missing",
            "userId": "user_missing",
            "sessionId": "session_123",
            "uiContext": {"module": "Billing"},
        },
    )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["requestId"] == "session_123"
    assert detail["status"] == "error"
    assert detail["error"]["code"] == "ENTITLEMENT_UNAVAILABLE"
    assert detail["error"]["safeUserMessage"] == (
        "I cannot answer that until your access is verified."
    )


def test_messages_endpoint_requires_auth() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/assistant/messages",
        json={
            "message": "Where do I submit monthly billing?",
            "tenantId": "tenant_123",
            "userId": "user_123",
            "sessionId": "session_123",
            "uiContext": {"module": "Billing"},
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "AUTH_REQUIRED"


def test_messages_endpoint_rejects_auth_body_mismatch() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/assistant/messages",
        headers={"Authorization": f"Bearer {_token(tenant_id='tenant_123', user_id='user_123')}"},
        json={
            "message": "Where do I submit monthly billing?",
            "tenantId": "tenant_999",
            "userId": "user_123",
            "sessionId": "session_123",
            "uiContext": {"module": "Billing"},
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "AUTH_REQUIRED"


def _token(tenant_id: str = "tenant_123", user_id: str = "user_123") -> str:
    return create_local_dev_token(tenant_id=tenant_id, user_id=user_id)
