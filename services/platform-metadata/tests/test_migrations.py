from __future__ import annotations

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "services" / "platform-metadata" / "alembic.ini"
MIGRATIONS = ROOT / "services" / "platform-metadata" / "migrations"


def test_platform_metadata_migration_builds_expected_schema(tmp_path) -> None:
    db_path = tmp_path / "platform-metadata.db"
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(config, "head")

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        observability_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(observability_events)")
        }
        observability_indexes = {
            row[1] for row in connection.execute("PRAGMA index_list(observability_events)")
        }

    assert {
        "tenants",
        "users",
        "release_versions",
        "eval_runs",
        "cost_events",
        "observability_events",
    }.issubset(tables)
    assert {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "request_id",
        "trace_id",
        "producer",
        "tenant_id",
        "user_id",
        "route",
        "payload_json",
    }.issubset(observability_columns)
    assert {
        "ix_observability_events_type_occurred",
        "ix_observability_events_request_trace",
        "ix_observability_events_tenant_occurred",
    }.issubset(observability_indexes)
