from __future__ import annotations

import pytest
from aegis_shared.contracts import ChatRequest
from assistant_api.auth import IdentityMismatchError, authenticate_request
from auth_service.local_tokens import AuthError, create_local_dev_token


def test_authenticate_request_returns_matching_principal() -> None:
    token = create_local_dev_token(tenant_id="tenant_123", user_id="user_123")
    principal = authenticate_request(
        authorization=f"Bearer {token}",
        request=ChatRequest(
            message="Where do I submit monthly billing?",
            tenantId="tenant_123",
            userId="user_123",
            sessionId="session_123",
        ),
    )

    assert principal.tenant_id == "tenant_123"
    assert principal.user_id == "user_123"


def test_authenticate_request_rejects_missing_token() -> None:
    with pytest.raises(AuthError):
        authenticate_request(
            authorization=None,
            request=ChatRequest(
                message="Where do I submit monthly billing?",
                tenantId="tenant_123",
                userId="user_123",
                sessionId="session_123",
            ),
        )


def test_authenticate_request_rejects_identity_mismatch() -> None:
    token = create_local_dev_token(tenant_id="tenant_123", user_id="user_123")

    with pytest.raises(IdentityMismatchError):
        authenticate_request(
            authorization=f"Bearer {token}",
            request=ChatRequest(
                message="Where do I submit monthly billing?",
                tenantId="tenant_999",
                userId="user_123",
                sessionId="session_123",
            ),
        )
