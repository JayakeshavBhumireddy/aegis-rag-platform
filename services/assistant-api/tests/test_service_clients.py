from __future__ import annotations

import httpx
from aegis_shared.contracts import ChatRequest, UiContext
from assistant_api.cache import ExactAnswerCache
from assistant_api.orchestrator import answer_message_via_http
from assistant_api.service_clients import HttpAegisServiceClients
from assistant_api.settings import AssistantSettings


def test_answer_message_via_http_clients() -> None:
    observed_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path in {"/v1/audit/records", "/v1/cost/events"}:
            observed_paths.append(request.url.path)
            return httpx.Response(200, json={"event": {"eventId": "evt_test"}})
        if request.url.path == "/v1/entitlements/resolve":
            return httpx.Response(
                200,
                json={
                    "entitlementEnvelope": {
                        "tenantId": "tenant_123",
                        "userId": "user_123",
                        "region": "us",
                        "productVersion": "2026.2",
                        "licensedModules": ["Billing"],
                        "enabledFeatures": ["MonthlySubmission"],
                        "role": "TenantAdmin",
                        "permissions": ["Billing.View", "Billing.Submit"],
                        "licenseHash": "lic_hash",
                        "permissionHash": "perm_hash",
                        "dataAccessMode": "product_guidance_only",
                    }
                },
            )
        if request.url.path == "/v1/policy/evaluate":
            return httpx.Response(
                200,
                json={
                    "policyDecision": {
                        "decision": "allow",
                        "canRetrieve": True,
                        "canAnswer": True,
                        "canCache": True,
                        "mustEscalate": False,
                        "retrievalScope": {
                            "tenantId": "tenant_123",
                            "modules": ["Billing"],
                            "permissions": ["Billing.View", "Billing.Submit"],
                            "productVersion": "2026.2",
                            "trustLevel": "approved",
                            "region": "us",
                        },
                        "reasons": [],
                    }
                },
            )
        if request.url.path == "/v1/context/build":
            return httpx.Response(200, json={"contextPack": {"redactions": []}})
        if request.url.path == "/v1/retrieval/search":
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "chunkId": "doc_billing_monthly_submission#body",
                            "sourceId": "doc_billing_monthly_submission",
                            "title": "Monthly Submission Workflow",
                            "text": (
                                "To open Monthly Submission, go to "
                                "Billing > Monthly Submission."
                            ),
                            "score": 0.9,
                            "metadata": {"module": "Billing"},
                        }
                    ]
                },
            )
        if request.url.path == "/v1/llm/generate":
            return httpx.Response(
                200,
                json={
                    "answer": "To open Monthly Submission, go to Billing > Monthly Submission.",
                    "citations": [
                        {
                            "sourceId": "doc_billing_monthly_submission",
                            "chunkId": "doc_billing_monthly_submission#body",
                            "title": "Monthly Submission Workflow",
                        }
                    ],
                    "confidence": 0.9,
                },
            )
        if request.url.path == "/v1/verification/check":
            return httpx.Response(
                200,
                json={
                    "verification": {
                        "verified": True,
                        "grounded": True,
                        "citationsValid": True,
                        "permissionCompliant": True,
                        "piiSafe": True,
                        "confidence": 0.9,
                        "reasons": [],
                    }
                },
            )
        return httpx.Response(404)

    clients = HttpAegisServiceClients(
        AssistantSettings(dependency_mode="http"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = answer_message_via_http(
        ChatRequest(
            message="Where do I submit monthly billing?",
            tenantId="tenant_123",
            userId="user_123",
            sessionId="session_123",
            uiContext=UiContext(module="Billing"),
        ),
        clients=clients,
        exact_cache=ExactAnswerCache(),
    )

    assert response.route == "scoped_rag_http"
    assert response.citations
    assert "/v1/audit/records" in observed_paths
    assert "/v1/cost/events" in observed_paths


def test_observability_client_failures_do_not_block_http_answer() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path in {"/v1/audit/records", "/v1/cost/events"}:
            return httpx.Response(503, json={"error": "telemetry unavailable"})
        if request.url.path == "/v1/entitlements/resolve":
            return httpx.Response(
                200,
                json={
                    "entitlementEnvelope": {
                        "tenantId": "tenant_123",
                        "userId": "user_123",
                        "region": "us",
                        "productVersion": "2026.2",
                        "licensedModules": ["Billing"],
                        "enabledFeatures": ["MonthlySubmission"],
                        "role": "TenantAdmin",
                        "permissions": ["Billing.View", "Billing.Submit"],
                        "licenseHash": "lic_hash",
                        "permissionHash": "perm_hash",
                        "dataAccessMode": "product_guidance_only",
                    }
                },
            )
        if request.url.path == "/v1/policy/evaluate":
            return httpx.Response(
                200,
                json={
                    "policyDecision": {
                        "decision": "allow",
                        "canRetrieve": True,
                        "canAnswer": True,
                        "canCache": True,
                        "mustEscalate": False,
                        "retrievalScope": {
                            "tenantId": "tenant_123",
                            "modules": ["Billing"],
                            "permissions": ["Billing.View", "Billing.Submit"],
                            "productVersion": "2026.2",
                            "trustLevel": "approved",
                            "region": "us",
                        },
                        "reasons": [],
                    }
                },
            )
        if request.url.path == "/v1/context/build":
            return httpx.Response(200, json={"contextPack": {"redactions": []}})
        if request.url.path == "/v1/retrieval/search":
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "chunkId": "doc_billing_monthly_submission#body",
                            "sourceId": "doc_billing_monthly_submission",
                            "title": "Monthly Submission Workflow",
                            "text": (
                                "To open Monthly Submission, go to "
                                "Billing > Monthly Submission."
                            ),
                            "score": 0.9,
                            "metadata": {"module": "Billing"},
                        }
                    ]
                },
            )
        if request.url.path == "/v1/llm/generate":
            return httpx.Response(
                200,
                json={
                    "answer": "To open Monthly Submission, go to Billing > Monthly Submission.",
                    "citations": [
                        {
                            "sourceId": "doc_billing_monthly_submission",
                            "chunkId": "doc_billing_monthly_submission#body",
                            "title": "Monthly Submission Workflow",
                        }
                    ],
                    "confidence": 0.9,
                },
            )
        if request.url.path == "/v1/verification/check":
            return httpx.Response(
                200,
                json={
                    "verification": {
                        "verified": True,
                        "grounded": True,
                        "citationsValid": True,
                        "permissionCompliant": True,
                        "piiSafe": True,
                        "confidence": 0.9,
                        "reasons": [],
                    }
                },
            )
        return httpx.Response(404)

    clients = HttpAegisServiceClients(
        AssistantSettings(dependency_mode="http"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = answer_message_via_http(
        ChatRequest(
            message="Where do I submit monthly billing?",
            tenantId="tenant_123",
            userId="user_123",
            sessionId="session_123",
            uiContext=UiContext(module="Billing"),
        ),
        clients=clients,
        exact_cache=ExactAnswerCache(),
    )

    assert response.route == "scoped_rag_http"
    assert response.citations
