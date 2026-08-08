import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower().strip(".")


class ScanHistoryStore:
    def __init__(self, db_path: str, enabled: bool, retention_limit: int) -> None:
        self._db_path = db_path
        self._enabled = enabled
        self._retention_limit = retention_limit
        self._lock = threading.Lock()

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def initialize(self) -> None:
        if not self._enabled:
            return

        path = Path(self._db_path)
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    url TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    explanation_source TEXT NOT NULL,
                    report_json TEXT NOT NULL
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_scan_history_created_at ON scan_history(created_at)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_scan_history_domain ON scan_history(domain)")

    def save(self, report: dict[str, object]) -> int | None:
        if not self._enabled:
            return None

        self.initialize()
        url = str(report.get("url") or "")
        explanation_source = report.get("explanation_source", {})
        source = ""
        if isinstance(explanation_source, dict):
            source = str(explanation_source.get("source") or "")

        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO scan_history (
                    created_at,
                    url,
                    domain,
                    risk_score,
                    risk_level,
                    explanation_source,
                    report_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _utc_now(),
                    url,
                    _domain(url),
                    int(report.get("risk_score") or 0),
                    str(report.get("risk_level") or ""),
                    source,
                    json.dumps(report),
                ),
            )
            self._prune(connection)
            return int(cursor.lastrowid)

    def list_recent(self, limit: int = 50, domain: str | None = None) -> list[dict[str, object]]:
        if not self._enabled:
            return []

        self.initialize()
        normalized_limit = max(1, min(limit, 200))
        query = (
            "SELECT id, created_at, url, domain, risk_score, risk_level, explanation_source, report_json "
            "FROM scan_history"
        )
        params: list[object] = []
        if domain:
            query += " WHERE domain = ?"
            params.append(domain.lower().strip())
        query += " ORDER BY id DESC LIMIT ?"
        params.append(normalized_limit)

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [self._row_to_item(row) for row in rows]

    def get(self, scan_id: int) -> dict[str, object] | None:
        if not self._enabled:
            return None

        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, created_at, url, domain, risk_score, risk_level, explanation_source, report_json "
                "FROM scan_history WHERE id = ?",
                (scan_id,),
            ).fetchone()

        return self._row_to_item(row) if row else None

    def clear(self) -> int:
        if not self._enabled:
            return 0

        self.initialize()
        with self._lock, self._connect() as connection:
            cursor = connection.execute("DELETE FROM scan_history")
            return int(cursor.rowcount)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _prune(self, connection: sqlite3.Connection) -> None:
        if self._retention_limit <= 0:
            return

        connection.execute(
            """
            DELETE FROM scan_history
            WHERE id NOT IN (
                SELECT id FROM scan_history ORDER BY id DESC LIMIT ?
            )
            """,
            (self._retention_limit,),
        )

    def _row_to_item(self, row: sqlite3.Row) -> dict[str, object]:
        report = json.loads(str(row["report_json"]))
        return {
            "id": int(row["id"]),
            "created_at": str(row["created_at"]),
            "url": str(row["url"]),
            "domain": str(row["domain"]),
            "risk_score": int(row["risk_score"]),
            "risk_level": str(row["risk_level"]),
            "explanation_source": str(row["explanation_source"]),
            "report": report,
        }


scan_history_store = ScanHistoryStore(
    db_path=settings.scan_history_db_path,
    enabled=settings.scan_history_enabled,
    retention_limit=settings.scan_history_retention_limit,
)
