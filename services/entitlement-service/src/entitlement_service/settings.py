from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EntitlementSettings:
    store_mode: str = "memory"
    sqlite_path: str | None = None

    @classmethod
    def from_env(cls) -> EntitlementSettings:
        return cls(
            store_mode=os.getenv("AEGIS_ENTITLEMENT_STORE_MODE", "memory"),
            sqlite_path=os.getenv("AEGIS_ENTITLEMENT_SQLITE_PATH"),
        )
