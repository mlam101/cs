from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Iterator

from campsite_watch_models import Watch


class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    phone TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS watches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    park_code TEXT NOT NULL,
                    site_code TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    party_size INTEGER NOT NULL,
                    check_frequency_minutes INTEGER NOT NULL DEFAULT 10,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watch_id INTEGER NOT NULL,
                    checked_at TEXT NOT NULL,
                    raw_response_json TEXT NOT NULL,
                    is_available INTEGER NOT NULL,
                    available_dates_json TEXT NOT NULL,
                    FOREIGN KEY (watch_id) REFERENCES watches(id)
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watch_id INTEGER NOT NULL,
                    sent_at TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    message TEXT NOT NULL,
                    availability_hash TEXT NOT NULL,
                    FOREIGN KEY (watch_id) REFERENCES watches(id)
                );
                """
            )

    def ensure_user(self, email: str, phone: str | None = None) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if row:
                return int(row["id"])
            cursor = conn.execute(
                "INSERT INTO users (email, phone, created_at) VALUES (?, ?, ?)",
                (email, phone, datetime.now(UTC).isoformat()),
            )
            return int(cursor.lastrowid)

    def create_watch(
        self,
        *,
        user_id: int,
        park_code: str,
        site_code: str,
        start_date: date,
        end_date: date,
        party_size: int,
        check_frequency_minutes: int,
        active: bool = True,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO watches (
                    user_id, park_code, site_code, start_date, end_date,
                    party_size, check_frequency_minutes, active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    park_code,
                    site_code,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    party_size,
                    check_frequency_minutes,
                    1 if active else 0,
                    datetime.now(UTC).isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def list_watches(self, *, user_id: int) -> list[Watch]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM watches WHERE user_id = ? ORDER BY id DESC", (user_id,)
            ).fetchall()
            return [self._watch_from_row(row) for row in rows]

    def get_watch(self, watch_id: int) -> Watch | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM watches WHERE id = ?", (watch_id,)).fetchone()
            if not row:
                return None
            return self._watch_from_row(row)

    def list_active_watches(self) -> list[Watch]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM watches WHERE active = 1").fetchall()
            return [self._watch_from_row(row) for row in rows]

    def set_watch_active(self, watch_id: int, active: bool) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE watches SET active = ? WHERE id = ?",
                (1 if active else 0, watch_id),
            )
            return cursor.rowcount > 0

    def create_check(
        self,
        *,
        watch_id: int,
        checked_at: datetime,
        raw_response: dict,
        is_available: bool,
        available_dates: list[str],
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO checks (
                    watch_id, checked_at, raw_response_json, is_available, available_dates_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    watch_id,
                    checked_at.isoformat(),
                    json.dumps(raw_response),
                    1 if is_available else 0,
                    json.dumps(available_dates),
                ),
            )
            return int(cursor.lastrowid)

    def get_previous_state(self, watch_id: int) -> bool | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT is_available
                FROM checks
                WHERE watch_id = ?
                ORDER BY checked_at DESC
                LIMIT 1 OFFSET 1
                """,
                (watch_id,),
            ).fetchone()
            if not row:
                return None
            return bool(row["is_available"])

    def list_checks(self, watch_id: int, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, watch_id, checked_at, is_available, available_dates_json
                FROM checks WHERE watch_id = ? ORDER BY checked_at DESC LIMIT ?
                """,
                (watch_id, limit),
            ).fetchall()
            return [
                {
                    "id": int(row["id"]),
                    "watch_id": int(row["watch_id"]),
                    "checked_at": row["checked_at"],
                    "is_available": bool(row["is_available"]),
                    "available_dates": json.loads(row["available_dates_json"]),
                }
                for row in rows
            ]

    def create_alert(
        self,
        *,
        watch_id: int,
        sent_at: datetime,
        channel: str,
        message: str,
        availability_hash: str,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alerts (watch_id, sent_at, channel, message, availability_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (watch_id, sent_at.isoformat(), channel, message, availability_hash),
            )
            return int(cursor.lastrowid)

    def has_alert_hash(self, watch_id: int, availability_hash: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM alerts WHERE watch_id = ? AND availability_hash = ? LIMIT 1",
                (watch_id, availability_hash),
            ).fetchone()
            return row is not None

    def list_alerts(self, watch_id: int, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, watch_id, sent_at, channel, message, availability_hash
                FROM alerts WHERE watch_id = ? ORDER BY sent_at DESC LIMIT ?
                """,
                (watch_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def _watch_from_row(row: sqlite3.Row) -> Watch:
        return Watch(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            park_code=str(row["park_code"]),
            site_code=str(row["site_code"]),
            start_date=date.fromisoformat(row["start_date"]),
            end_date=date.fromisoformat(row["end_date"]),
            party_size=int(row["party_size"]),
            check_frequency_minutes=int(row["check_frequency_minutes"]),
            active=bool(row["active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
