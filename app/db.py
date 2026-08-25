from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(
    os.getenv(
        "ASA_AOIP_DB_PATH",
        "/data/asa_aoip.db" if os.getenv("RENDER") else "asa_aoip.db",
    )
)
_SQLITE_TIMEOUT_SECONDS = 5.0
_SQLITE_BUSY_TIMEOUT_MS = 5_000
_MIN_AUDIT_HMAC_KEY_LENGTH = 32
_AUDIT_CHAIN_VERSION = "hmac-sha256-chain-v1"
_LEGACY_AUDIT_CHAIN_VERSION = "legacy-unchained-v0"
_AUDIT_CHAIN_KEY_DOMAIN = b"ASA-AI-AUDIT-CHAIN-KEY/v1"


def _audit_chain_key() -> bytes:
    raw = os.getenv("ASA_AUDIT_HMAC_KEY", "")
    if len(raw) < _MIN_AUDIT_HMAC_KEY_LENGTH:
        raise RuntimeError("AI audit HMAC key is not securely configured")
    return hmac.new(
        raw.encode("utf-8"),
        _AUDIT_CHAIN_KEY_DOMAIN,
        hashlib.sha256,
    ).digest()


def _audit_event_hash(
    question_hash: str,
    question_fingerprint_version: str,
    question_data_origin: str,
    event_status: str,
    model: str,
    evidence_ids: str,
    prev_event_hash: str,
    created_at: str,
) -> str:
    material = json.dumps(
        {
            "created_at": created_at,
            "evidence_ids": evidence_ids,
            "event_integrity_version": _AUDIT_CHAIN_VERSION,
            "model": model,
            "prev_event_hash": prev_event_hash,
            "question_data_origin": question_data_origin,
            "question_fingerprint_version": question_fingerprint_version,
            "question_hash": question_hash,
            "status": event_status,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(_audit_chain_key(), material, hashlib.sha256).hexdigest()


def _connect() -> sqlite3.Connection:
    """Open a bounded SQLite connection with explicit safety/durability controls."""
    conn = sqlite3.connect(DB_PATH, timeout=_SQLITE_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA synchronous = FULL")
    conn.create_function("asa_audit_event_hash", 8, _audit_event_hash)
    return conn


def _ensure_column(conn: sqlite3.Connection, name: str, definition: str) -> None:
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(knowledge_items)").fetchall()
    }
    if name not in columns:
        conn.execute(f"ALTER TABLE knowledge_items ADD COLUMN {name} {definition}")


def _ensure_ai_audit_column(
    conn: sqlite3.Connection, name: str, definition: str
) -> None:
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(ai_audit_events)").fetchall()
    }
    if name not in columns:
        conn.execute(f"ALTER TABLE ai_audit_events ADD COLUMN {name} {definition}")


def _install_ai_audit_chain_trigger(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TRIGGER IF EXISTS ai_audit_events_chain_v1")
    conn.execute(
        f"""
        CREATE TRIGGER ai_audit_events_chain_v1
        AFTER INSERT ON ai_audit_events
        BEGIN
            UPDATE ai_audit_events
            SET prev_event_hash = COALESCE(
                    (
                        SELECT event_hash
                        FROM ai_audit_events
                        WHERE id < NEW.id
                          AND event_integrity_version = '{_AUDIT_CHAIN_VERSION}'
                        ORDER BY id DESC
                        LIMIT 1
                    ),
                    ''
                ),
                event_integrity_version = '{_AUDIT_CHAIN_VERSION}',
                event_hash = asa_audit_event_hash(
                    NEW.question_hash,
                    NEW.question_fingerprint_version,
                    NEW.question_data_origin,
                    NEW.status,
                    NEW.model,
                    NEW.evidence_ids,
                    COALESCE(
                        (
                            SELECT event_hash
                            FROM ai_audit_events
                            WHERE id < NEW.id
                              AND event_integrity_version = '{_AUDIT_CHAIN_VERSION}'
                            ORDER BY id DESC
                            LIMIT 1
                        ),
                        ''
                    ),
                    NEW.created_at
                )
            WHERE id = NEW.id;
        END
        """
    )


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _connect()
    try:
        journal_mode = conn.execute("PRAGMA journal_mode = WAL").fetchone()[0]
        if str(journal_mode).lower() != "wal":
            raise RuntimeError("SQLite WAL mode could not be enabled")

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
                provenance_version TEXT NOT NULL DEFAULT 'legacy-v0',
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
                question_fingerprint_version TEXT NOT NULL DEFAULT 'sha256-v0',
                question_data_origin TEXT NOT NULL DEFAULT 'unverified_legacy',
                status TEXT NOT NULL,
                model TEXT NOT NULL DEFAULT '',
                evidence_ids TEXT NOT NULL DEFAULT '',
                prev_event_hash TEXT NOT NULL DEFAULT '',
                event_hash TEXT NOT NULL DEFAULT '',
                event_integrity_version TEXT NOT NULL DEFAULT 'legacy-unchained-v0',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _ensure_column(conn, "source_type", "TEXT NOT NULL DEFAULT 'text'")
        _ensure_column(conn, "purpose", "TEXT NOT NULL DEFAULT 'knowledge_management'")
        _ensure_column(conn, "sensitivity", "TEXT NOT NULL DEFAULT 'internal'")
        _ensure_column(conn, "transformation_state", "TEXT NOT NULL DEFAULT 'original'")
        _ensure_column(
            conn, "data_origin", "TEXT NOT NULL DEFAULT 'unverified_legacy'"
        )
        _ensure_column(conn, "approval_reference", "TEXT")
        _ensure_column(conn, "provenance_hash", "TEXT NOT NULL DEFAULT ''")
        # Pre-versioning rows retain their historical hash semantics. They are
        # not silently recomputed or promoted to the canonical algorithm.
        _ensure_column(
            conn,
            "provenance_version",
            "TEXT NOT NULL DEFAULT 'legacy-v0'",
        )
        _ensure_ai_audit_column(
            conn,
            "question_data_origin",
            "TEXT NOT NULL DEFAULT 'unverified_legacy'",
        )
        # Existing audit rows retain their historical fingerprint semantics.
        _ensure_ai_audit_column(
            conn,
            "question_fingerprint_version",
            "TEXT NOT NULL DEFAULT 'sha256-v0'",
        )
        # Existing rows predate event chaining. Preserve them as legacy instead
        # of inventing integrity evidence retroactively.
        _ensure_ai_audit_column(conn, "prev_event_hash", "TEXT NOT NULL DEFAULT ''")
        _ensure_ai_audit_column(conn, "event_hash", "TEXT NOT NULL DEFAULT ''")
        _ensure_ai_audit_column(
            conn,
            "event_integrity_version",
            "TEXT NOT NULL DEFAULT 'legacy-unchained-v0'",
        )
        _install_ai_audit_chain_trigger(conn)
        conn.commit()
    finally:
        conn.close()


def verify_ai_audit_chain() -> dict[str, int | str | bool | None]:
    """Verify chained AI audit events without rewriting historical legacy rows."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM ai_audit_events ORDER BY id").fetchall()

    previous_hash = ""
    chain_started = False
    legacy_events = 0
    verified_events = 0

    for row in rows:
        version = row["event_integrity_version"]
        event_id = int(row["id"])

        if version == _LEGACY_AUDIT_CHAIN_VERSION:
            if chain_started or row["prev_event_hash"] or row["event_hash"]:
                return {
                    "ok": False,
                    "legacy_events": legacy_events,
                    "verified_events": verified_events,
                    "first_invalid_id": event_id,
                    "reason": "invalid_legacy_boundary",
                }
            legacy_events += 1
            continue

        if version != _AUDIT_CHAIN_VERSION:
            return {
                "ok": False,
                "legacy_events": legacy_events,
                "verified_events": verified_events,
                "first_invalid_id": event_id,
                "reason": "unsupported_integrity_version",
            }

        chain_started = True
        if row["prev_event_hash"] != previous_hash:
            return {
                "ok": False,
                "legacy_events": legacy_events,
                "verified_events": verified_events,
                "first_invalid_id": event_id,
                "reason": "previous_hash_mismatch",
            }

        expected_hash = _audit_event_hash(
            row["question_hash"],
            row["question_fingerprint_version"],
            row["question_data_origin"],
            row["status"],
            row["model"],
            row["evidence_ids"],
            row["prev_event_hash"],
            row["created_at"],
        )
        if not hmac.compare_digest(row["event_hash"], expected_hash):
            return {
                "ok": False,
                "legacy_events": legacy_events,
                "verified_events": verified_events,
                "first_invalid_id": event_id,
                "reason": "event_hash_mismatch",
            }

        previous_hash = row["event_hash"]
        verified_events += 1

    return {
        "ok": True,
        "legacy_events": legacy_events,
        "verified_events": verified_events,
        "first_invalid_id": None,
        "reason": "verified",
    }


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()
