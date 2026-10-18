"""SQLite-backed append-only event ledger."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


class EventLedger:
    """Persist structured runtime events and commit each append before returning."""

    def __init__(self, database_path: str | Path = "agentic-runtime.db") -> None:
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._connection:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS runtime_events ("
                "event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, "
                "event_type TEXT NOT NULL, payload_json TEXT NOT NULL, occurred_at TEXT NOT NULL)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_runtime_events_run_id "
                "ON runtime_events(run_id, event_id)"
            )

    def append(self, run_id: str, event_type: str, payload: dict[str, Any]) -> int:
        occurred_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT INTO runtime_events(run_id, event_type, payload_json, occurred_at) "
                "VALUES (?, ?, ?, ?)",
                (run_id, event_type, json.dumps(payload, sort_keys=True), occurred_at),
            )
            return int(cursor.lastrowid)

    def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT event_id, run_id, event_type, payload_json, occurred_at "
                "FROM runtime_events WHERE run_id = ? ORDER BY event_id", (run_id,)
            ).fetchall()
        return [
            {"event_id": row["event_id"], "run_id": row["run_id"],
             "event_type": row["event_type"], "payload": json.loads(row["payload_json"]),
             "occurred_at": row["occurred_at"]}
            for row in rows
        ]

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> "EventLedger":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
