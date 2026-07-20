from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any

from aegis_shared.contracts import AuthenticatedPrincipal

TOKEN_PREFIX = "aegis.v1"
DEFAULT_ISSUER = "aegis-local-dev"


class AuthError(RuntimeError):
    """Raised when authentication cannot be established safely."""


@dataclass(frozen=True)
class LocalAuthSettings:
    issuer: str = DEFAULT_ISSUER
    secret: str = "aegis-local-dev-secret"

    @classmethod
    def from_env(cls) -> LocalAuthSettings:
        return cls(
            issuer=os.getenv("AEGIS_AUTH_ISSUER", DEFAULT_ISSUER),
            secret=os.getenv("AEGIS_AUTH_DEV_SECRET", cls.secret),
        )


def create_local_dev_token(
    *,
    tenant_id: str,
    user_id: str,
    subject: str | None = None,
    roles: list[str] | None = None,
    settings: LocalAuthSettings | None = None,
) -> str:
    active_settings = settings or LocalAuthSettings.from_env()
    payload = {
        "iss": active_settings.issuer,
        "sub": subject or user_id,
        "tenantId": tenant_id,
        "userId": user_id,
        "roles": roles or [],
    }
    encoded_payload = _b64_json(payload)
    signature = _sign(encoded_payload, active_settings.secret)
    return f"{TOKEN_PREFIX}.{encoded_payload}.{signature}"


def authenticate_bearer_token(
    authorization: str | None,
    *,
    settings: LocalAuthSettings | None = None,
) -> AuthenticatedPrincipal:
    if not authorization:
        raise AuthError("authorization header is required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError("bearer token is required")
    return validate_local_dev_token(token, settings=settings)


def validate_local_dev_token(
    token: str,
    *,
    settings: LocalAuthSettings | None = None,
) -> AuthenticatedPrincipal:
    active_settings = settings or LocalAuthSettings.from_env()
    parts = token.split(".")
    if len(parts) != 4 or ".".join(parts[:2]) != TOKEN_PREFIX:
        raise AuthError("unsupported token format")

    encoded_payload = parts[2]
    signature = parts[3]
    expected_signature = _sign(encoded_payload, active_settings.secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthError("token signature is invalid")

    payload = _decode_payload(encoded_payload)
    if payload.get("iss") != active_settings.issuer:
        raise AuthError("token issuer is invalid")

    try:
        return AuthenticatedPrincipal(
            subject=str(payload["sub"]),
            tenantId=str(payload["tenantId"]),
            userId=str(payload["userId"]),
            roles=[str(role) for role in payload.get("roles", [])],
            issuer=str(payload["iss"]),
        )
    except KeyError as exc:
        raise AuthError("token payload is incomplete") from exc


def _b64_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_payload(encoded_payload: str) -> dict[str, Any]:
    padding = "=" * (-len(encoded_payload) % 4)
    try:
        raw = base64.urlsafe_b64decode((encoded_payload + padding).encode("ascii"))
        value = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise AuthError("token payload is invalid") from exc
    if not isinstance(value, dict):
        raise AuthError("token payload must be an object")
    return value


def _sign(encoded_payload: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
