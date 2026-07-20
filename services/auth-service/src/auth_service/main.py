from __future__ import annotations

from aegis_shared.contracts import AuthenticatedPrincipal
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from auth_service.local_tokens import AuthError, validate_local_dev_token

SERVICE_VERSION = "auth-service-v0"

app = FastAPI(title="AegisRAG auth-service", version=SERVICE_VERSION)


class AuthValidateRequest(BaseModel):
    token: str


class AuthValidateResponse(BaseModel):
    principal: AuthenticatedPrincipal


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/auth/validate", response_model=AuthValidateResponse)
def validate(request: AuthValidateRequest) -> AuthValidateResponse:
    try:
        return AuthValidateResponse(principal=validate_local_dev_token(request.token))
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_REQUIRED", "message": "Authentication failed."},
        ) from exc
