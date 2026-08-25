from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.getenv("ASA_AOIP_DB_PATH", "/data/asa_aoip.db" if os.getenv("RENDER") else "asa_aoip.db"))


def _ensure_column(conn: sqlite3.Connection, name: str, definition: str) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(knowledge_items)").fetchall()}
    if name not in columns:
        conn.execute(f"ALTER TABLE knowledge_items ADD COLUMN {name} {definition}")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                source_type TEXT NOT NULL DEFAULT 'text',
                purpose TEXT NOT NULL DEFAULT 'knowledge_management',
                sensitivity TEXT NOT NULL DEFAULT 'internal',
                transformation_state TEXT NOT NULL DEFAULT 'original',
                data_origin TEXT NOT NULL DEFAULT 'unverified_legacy',
                approval_reference TEXT,
                provenance_hash TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                model TEXT NOT NULL DEFAULT '',
                evidence_ids TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _ensure_column(conn, "source_type", "TEXT NOT NULL DEFAULT 'text'")
        _ensure_column(conn, "purpose", "TEXT NOT NULL DEFAULT 'knowledge_management'")
        _ensure_column(conn, "sensitivity", "TEXT NOT NULL DEFAULT 'internal'")
        _ensure_column(conn, "transformation_state", "TEXT NOT NULL DEFAULT 'original'")
        # A pre-existing row has no independently verified origin. Mark it
        # unverified instead of silently promoting it to synthetic/public/approved.
        _ensure_column(conn, "data_origin", "TEXT NOT NULL DEFAULT 'unverified_legacy'")
        _ensure_column(conn, "approval_reference", "TEXT")
        _ensure_column(conn, "provenance_hash", "TEXT NOT NULL DEFAULT ''")
        conn.commit()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
