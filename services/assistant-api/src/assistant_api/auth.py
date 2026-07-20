from __future__ import annotations

from aegis_shared.contracts import AuthenticatedPrincipal, ChatRequest
from auth_service.local_tokens import AuthError, authenticate_bearer_token


class IdentityMismatchError(AuthError):
    """Raised when an authenticated principal does not match the request body."""


def authenticate_request(
    *,
    authorization: str | None,
    request: ChatRequest,
) -> AuthenticatedPrincipal:
    principal = authenticate_bearer_token(authorization)
    if principal.tenant_id != request.tenant_id or principal.user_id != request.user_id:
        raise IdentityMismatchError("authenticated principal does not match request body")
    return principal
