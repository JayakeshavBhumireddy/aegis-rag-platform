from __future__ import annotations

from aegis_shared.contracts import ErrorCode
from aegis_shared.runtime import build_error_response, new_request_context


def test_new_request_context_uses_contract_shape() -> None:
    context = new_request_context(caller="assistant-api", request_id="req_known")

    assert context.request_id == "req_known"
    assert context.trace_id.startswith("trace_")
    assert context.contract_version == "v1"


def test_build_error_response_matches_contract() -> None:
    response = build_error_response(
        request_id="req_123",
        code=ErrorCode.POLICY_DENIED,
        message="Denied.",
        safe_user_message="I cannot answer that with your current access.",
        retryable=False,
    )

    body = response.model_dump(by_alias=True, mode="json")
    assert body["requestId"] == "req_123"
    assert body["status"] == "error"
    assert body["error"]["code"] == "POLICY_DENIED"
    assert body["error"]["retryable"] is False
