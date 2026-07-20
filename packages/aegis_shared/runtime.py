from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aegis_shared.contracts import ErrorCode, ErrorDetail, ErrorResponse, RequestContext


def new_request_context(*, caller: str, request_id: str | None = None) -> RequestContext:
    return RequestContext(
        requestId=request_id or f"req_{uuid4().hex}",
        traceId=f"trace_{uuid4().hex}",
        timestamp=datetime.now(UTC),
        caller=caller,
        contractVersion="v1",
    )


def build_error_response(
    *,
    request_id: str,
    code: ErrorCode,
    message: str,
    safe_user_message: str,
    retryable: bool,
    details: dict | None = None,
) -> ErrorResponse:
    return ErrorResponse(
        requestId=request_id,
        error=ErrorDetail(
            code=code,
            message=message,
            retryable=retryable,
            safeUserMessage=safe_user_message,
            details=details or {},
        ),
    )
