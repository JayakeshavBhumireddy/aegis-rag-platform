from __future__ import annotations

from aegis_shared.contracts import ChatRequest, ChatResponse, ErrorCode
from aegis_shared.runtime import build_error_response
from auth_service.local_tokens import AuthError
from entitlement_service.resolver import EntitlementResolutionError
from fastapi import FastAPI, Header, HTTPException, status

from assistant_api.auth import authenticate_request
from assistant_api.orchestrator import answer_message, answer_message_via_http
from assistant_api.service_clients import DependencyUnavailableError, HttpAegisServiceClients
from assistant_api.settings import AssistantSettings

SERVICE_VERSION = "assistant-api-v0"

app = FastAPI(title="AegisRAG assistant-api", version=SERVICE_VERSION)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/v1/assistant/messages", response_model=ChatResponse)
def messages(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
) -> ChatResponse:
    settings = AssistantSettings.from_env()
    request_id = request.session_id
    try:
        principal = authenticate_request(authorization=authorization, request=request)
        if settings.dependency_mode == "http":
            return answer_message_via_http(
                request,
                principal=principal,
                clients=HttpAegisServiceClients(settings),
            )
        return answer_message(request, principal=principal)
    except AuthError as exc:
        error = build_error_response(
            request_id=request_id,
            code=ErrorCode.AUTH_REQUIRED,
            message="Authentication failed.",
            safe_user_message="Please sign in before using the assistant.",
            retryable=False,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.model_dump(by_alias=True, mode="json"),
        ) from exc
    except EntitlementResolutionError as exc:
        error = build_error_response(
            request_id=request_id,
            code=ErrorCode.ENTITLEMENT_UNAVAILABLE,
            message="Entitlement envelope could not be resolved.",
            safe_user_message="I cannot answer that until your access is verified.",
            retryable=True,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.model_dump(by_alias=True, mode="json"),
        ) from exc
    except DependencyUnavailableError as exc:
        error = build_error_response(
            request_id=request_id,
            code=ErrorCode.DEPENDENCY_UNAVAILABLE,
            message="A required assistant dependency is unavailable.",
            safe_user_message="A required assistant service is temporarily unavailable.",
            retryable=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error.model_dump(by_alias=True, mode="json"),
        ) from exc
