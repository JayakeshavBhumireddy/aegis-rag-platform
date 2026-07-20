from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantSettings:
    dependency_mode: str = "local"
    entitlement_url: str = "http://localhost:8011"
    policy_url: str = "http://localhost:8012"
    context_url: str = "http://localhost:8013"
    retrieval_url: str = "http://localhost:8014"
    llm_gateway_url: str = "http://localhost:8015"
    verification_url: str = "http://localhost:8016"
    observability_url: str = "http://localhost:8017"
    request_timeout_seconds: float = 3.0

    @classmethod
    def from_env(cls) -> AssistantSettings:
        return cls(
            dependency_mode=os.getenv("AEGIS_ASSISTANT_DEPENDENCY_MODE", "local"),
            entitlement_url=os.getenv("AEGIS_ENTITLEMENT_URL", cls.entitlement_url),
            policy_url=os.getenv("AEGIS_POLICY_URL", cls.policy_url),
            context_url=os.getenv("AEGIS_CONTEXT_URL", cls.context_url),
            retrieval_url=os.getenv("AEGIS_RETRIEVAL_URL", cls.retrieval_url),
            llm_gateway_url=os.getenv("AEGIS_LLM_GATEWAY_URL", cls.llm_gateway_url),
            verification_url=os.getenv("AEGIS_VERIFICATION_URL", cls.verification_url),
            observability_url=os.getenv("AEGIS_OBSERVABILITY_URL", cls.observability_url),
            request_timeout_seconds=float(os.getenv("AEGIS_REQUEST_TIMEOUT_SECONDS", "3.0")),
        )
