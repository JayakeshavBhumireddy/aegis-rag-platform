from __future__ import annotations

import pytest
from auth_service.local_tokens import (
    AuthError,
    LocalAuthSettings,
    authenticate_bearer_token,
    create_local_dev_token,
    validate_local_dev_token,
)


def test_creates_and_validates_local_dev_token() -> None:
    settings = LocalAuthSettings(secret="test-secret")
    token = create_local_dev_token(
        tenant_id="tenant_123",
        user_id="user_123",
        subject="subject_123",
        roles=["TenantAdmin"],
        settings=settings,
    )

    principal = validate_local_dev_token(token, settings=settings)

    assert principal.tenant_id == "tenant_123"
    assert principal.user_id == "user_123"
    assert principal.subject == "subject_123"
    assert principal.roles == ["TenantAdmin"]


def test_rejects_tampered_token_signature() -> None:
    settings = LocalAuthSettings(secret="test-secret")
    token = create_local_dev_token(
        tenant_id="tenant_123",
        user_id="user_123",
        settings=settings,
    )

    with pytest.raises(AuthError):
        validate_local_dev_token(f"{token}x", settings=settings)


def test_authenticate_bearer_token_requires_bearer_scheme() -> None:
    with pytest.raises(AuthError):
        authenticate_bearer_token("Basic token")
