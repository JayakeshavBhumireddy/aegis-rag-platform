from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from aegis_shared.contracts import EventEnvelope, EventType


class SQLiteEventEnvelopeRepository:
    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def record(self, event: EventEnvelope) -> EventEnvelope:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO observability_events (
                    event_id,
                    event_type,
                    occurred_at,
                    request_id,
                    trace_id,
                    producer,
                    envelope_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.event_type.value,
                    event.occurred_at.isoformat(),
                    event.request_id,
                    event.trace_id,
                    event.producer,
                    json.dumps(event.model_dump(by_alias=True, mode="json"), sort_keys=True),
                ),
            )
        return event

    def list_events(self, event_type: EventType | None = None) -> list[EventEnvelope]:
        sql = "SELECT envelope_json FROM observability_events"
        parameters: tuple[str, ...] = ()
        if event_type is not None:
            sql += " WHERE event_type = ?"
            parameters = (event_type.value,)
        sql += " ORDER BY occurred_at ASC, event_id ASC"
        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [EventEnvelope.model_validate(json.loads(row["envelope_json"])) for row in rows]

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM observability_events")

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS observability_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    producer TEXT NOT NULL,
                    envelope_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_observability_events_type_occurred
                ON observability_events (event_type, occurred_at)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_observability_events_request
                ON observability_events (request_id)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection
