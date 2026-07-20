from __future__ import annotations

from typing import Any

ROUTE_USAGE_ESTIMATES: dict[str, dict[str, Any]] = {
    "exact_cache": {
        "estimatedLatencyMs": 25,
        "estimatedCostUsd": 0.0,
        "provider": "local-cache",
    },
    "navigation_graph": {
        "estimatedLatencyMs": 80,
        "estimatedCostUsd": 0.0001,
        "provider": "local-navigation-graph",
    },
    "scoped_rag_local": {
        "estimatedLatencyMs": 500,
        "estimatedCostUsd": 0.001,
        "provider": "local-hybrid-retrieval",
    },
    "scoped_rag_http": {
        "estimatedLatencyMs": 900,
        "estimatedCostUsd": 0.002,
        "provider": "local-http-services",
    },
    "retrieval_empty": {
        "estimatedLatencyMs": 250,
        "estimatedCostUsd": 0.0002,
        "provider": "local-hybrid-retrieval",
    },
    "verification_failed": {
        "estimatedLatencyMs": 700,
        "estimatedCostUsd": 0.001,
        "provider": "local-verifier",
    },
    "denial_or_escalation": {
        "estimatedLatencyMs": 50,
        "estimatedCostUsd": 0.0,
        "provider": "local-policy",
    },
}


def estimate_usage(route: str, *, input_text: str = "", output_text: str = "") -> dict[str, Any]:
    baseline = ROUTE_USAGE_ESTIMATES.get(
        route,
        {
            "estimatedLatencyMs": 1000,
            "estimatedCostUsd": 0.005,
            "provider": "unknown",
        },
    )
    input_tokens = _estimate_tokens(input_text)
    output_tokens = _estimate_tokens(output_text)
    return {
        **baseline,
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "route": route,
        "currency": "USD",
    }


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, round(len(text.split()) * 1.3))
