from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ObservabilitySettings:
    store_mode: str = "memory"
    sqlite_path: str | None = None

    @classmethod
    def from_env(cls) -> ObservabilitySettings:
        return cls(
            store_mode=os.getenv("AEGIS_OBSERVABILITY_STORE_MODE", "memory"),
            sqlite_path=os.getenv("AEGIS_OBSERVABILITY_SQLITE_PATH"),
        )

    def resolved_sqlite_path(self) -> Path:
        if not self.sqlite_path:
            raise ValueError("sqlite observability store requires AEGIS_OBSERVABILITY_SQLITE_PATH")
        return Path(self.sqlite_path)
