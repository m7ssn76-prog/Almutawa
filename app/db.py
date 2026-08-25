from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
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
_AUDIT_STATE_VERSION = "hmac-sha256-state-v1"
_AUDIT_CHAIN_KEY_DOMAIN = b"ASA-AI-AUDIT-CHAIN-KEY/v1"
_AUDIT_STATE_KEY_DOMAIN = b"ASA-AI-AUDIT-STATE-KEY/v1"


def _audit_root_key() -> bytes:
    raw = os.getenv("ASA_AUDIT_HMAC_KEY", "")
    if len(raw) < _MIN_AUDIT_HMAC_KEY_LENGTH:
        raise RuntimeError("AI audit HMAC key is not securely configured")
    return raw.encode("utf-8")


def _audit_chain_key() -> bytes:
    return hmac.new(
        _audit_root_key(),
        _AUDIT_CHAIN_KEY_DOMAIN,
        hashlib.sha256,
    ).digest()


def _audit_state_key() -> bytes:
    return hmac.new(
        _audit_root_key(),
        _AUDIT_STATE_KEY_DOMAIN,
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


def _audit_state_hash(
    event_count: int,
    last_event_id: int,
    last_event_hash: str,
    updated_at: str,
) -> str:
    material = json.dumps(
        {
            "event_count": int(event_count),
            "last_event_hash": last_event_hash,
            "last_event_id": int(last_event_id),
            "state_version": _AUDIT_STATE_VERSION,
            "updated_at": updated_at,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(_audit_state_key(), material, hashlib.sha256).hexdigest()


def _connect() -> sqlite3.Connection:
    """Open a bounded SQLite connection with explicit safety/durability controls."""
    conn = sqlite3.connect(DB_PATH, timeout=_SQLITE_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA synchronous = FULL")
    conn.create_function("asa_audit_event_hash", 8, _audit_event_hash)
    conn.create_function("asa_audit_state_hash", 4, _audit_state_hash)
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
    # Keep this DDL completely static so no runtime value enters the SQL text.
    conn.execute(
        """
        CREATE TRIGGER ai_audit_events_chain_v1
        AFTER INSERT ON ai_audit_events
        BEGIN
            UPDATE ai_audit_events
            SET prev_event_hash = COALESCE(
                    (
                        SELECT event_hash
                        FROM ai_audit_events
                        WHERE id < NEW.id
                          AND event_integrity_version = 'hmac-sha256-chain-v1'
                        ORDER BY id DESC
                        LIMIT 1
                    ),
                    ''
                ),
                event_integrity_version = 'hmac-sha256-chain-v1',
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
                              AND event_integrity_version = 'hmac-sha256-chain-v1'
                            ORDER BY id DESC
                            LIMIT 1
                        ),
                        ''
                    ),
                    NEW.created_at
                )
            WHERE id = NEW.id;

            INSERT INTO ai_audit_chain_state (
                id, event_count, last_event_id, last_event_hash,
                state_hash, state_version, updated_at
            )
            SELECT
                1,
                COUNT(*),
                NEW.id,
                (SELECT event_hash FROM ai_audit_events WHERE id = NEW.id),
                asa_audit_state_hash(
                    COUNT(*),
                    NEW.id,
                    (SELECT event_hash FROM ai_audit_events WHERE id = NEW.id),
                    CURRENT_TIMESTAMP
                ),
                'hmac-sha256-state-v1',
                CURRENT_TIMESTAMP
            FROM ai_audit_events
            WHERE event_integrity_version = 'hmac-sha256-chain-v1'
            ON CONFLICT(id) DO UPDATE SET
                event_count = excluded.event_count,
                last_event_id = excluded.last_event_id,
                last_event_hash = excluded.last_event_hash,
                state_hash = excluded.state_hash,
                state_version = excluded.state_version,
                updated_at = excluded.updated_at;
        END
        """
    )


def _bootstrap_chain_state_if_possible(conn: sqlite3.Connection) -> None:
    existing = conn.execute(
        "SELECT id FROM ai_audit_chain_state WHERE id = 1"
    ).fetchone()
    if existing is not None:
        return

    summary = conn.execute(
        """
        SELECT COUNT(*) AS event_count,
               COALESCE(MAX(id), 0) AS last_event_id
        FROM ai_audit_events
        WHERE event_integrity_version = 'hmac-sha256-chain-v1'
        """
    ).fetchone()
    event_count = int(summary["event_count"])
    if event_count == 0:
        return

    # A pre-checkpoint database can be upgraded without rewriting its event
    # chain. If the audit key is unavailable, leave the missing checkpoint
    # visible to verification instead of manufacturing an unsigned state.
    try:
        _audit_state_key()
    except RuntimeError:
        return

    last_event_id = int(summary["last_event_id"])
    last_row = conn.execute(
        "SELECT event_hash FROM ai_audit_events WHERE id = ?",
        (last_event_id,),
    ).fetchone()
    last_event_hash = str(last_row["event_hash"])
    updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state_hash = _audit_state_hash(
        event_count,
        last_event_id,
        last_event_hash,
        updated_at,
    )
    conn.execute(
        """
        INSERT INTO ai_audit_chain_state (
            id, event_count, last_event_id, last_event_hash,
            state_hash, state_version, updated_at
        )
        VALUES (1, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_count,
            last_event_id,
            last_event_hash,
            state_hash,
            _AUDIT_STATE_VERSION,
            updated_at,
        ),
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_audit_chain_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                event_count INTEGER NOT NULL,
                last_event_id INTEGER NOT NULL,
                last_event_hash TEXT NOT NULL,
                state_hash TEXT NOT NULL,
                state_version TEXT NOT NULL,
                updated_at TEXT NOT NULL
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
        _ensure_ai_audit_column(
            conn,
            "question_fingerprint_version",
            "TEXT NOT NULL DEFAULT 'sha256-v0'",
        )
        _ensure_ai_audit_column(conn, "prev_event_hash", "TEXT NOT NULL DEFAULT ''")
        _ensure_ai_audit_column(conn, "event_hash", "TEXT NOT NULL DEFAULT ''")
        _ensure_ai_audit_column(
            conn,
            "event_integrity_version",
            "TEXT NOT NULL DEFAULT 'legacy-unchained-v0'",
        )
        _install_ai_audit_chain_trigger(conn)
        _bootstrap_chain_state_if_possible(conn)
        conn.commit()
    finally:
        conn.close()


def verify_ai_audit_chain() -> dict[str, int | str | bool | None]:
    """Verify chained events plus the signed chain checkpoint."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM ai_audit_events ORDER BY id").fetchall()
        state = conn.execute(
            "SELECT * FROM ai_audit_chain_state WHERE id = 1"
        ).fetchone()
        sequence_row = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name = 'ai_audit_events'"
        ).fetchone()

    sequence_value = int(sequence_row["seq"]) if sequence_row is not None else 0
    current_max_id = int(rows[-1]["id"]) if rows else 0
    if sequence_value > current_max_id:
        return {
            "ok": False,
            "legacy_events": 0,
            "verified_events": 0,
            "first_invalid_id": None,
            "reason": "audit_tail_gap_detected",
        }

    previous_hash = ""
    last_chain_id = 0
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
        last_chain_id = event_id
        verified_events += 1

    if verified_events == 0:
        if state is not None:
            return {
                "ok": False,
                "legacy_events": legacy_events,
                "verified_events": 0,
                "first_invalid_id": None,
                "reason": "orphaned_chain_checkpoint",
            }
        return {
            "ok": True,
            "legacy_events": legacy_events,
            "verified_events": 0,
            "first_invalid_id": None,
            "reason": "verified",
        }

    if state is None:
        return {
            "ok": False,
            "legacy_events": legacy_events,
            "verified_events": verified_events,
            "first_invalid_id": None,
            "reason": "missing_chain_checkpoint",
        }
    if state["state_version"] != _AUDIT_STATE_VERSION:
        return {
            "ok": False,
            "legacy_events": legacy_events,
            "verified_events": verified_events,
            "first_invalid_id": None,
            "reason": "unsupported_checkpoint_version",
        }
    if int(state["event_count"]) != verified_events:
        return {
            "ok": False,
            "legacy_events": legacy_events,
            "verified_events": verified_events,
            "first_invalid_id": None,
            "reason": "checkpoint_count_mismatch",
        }
    if int(state["last_event_id"]) != last_chain_id:
        return {
            "ok": False,
            "legacy_events": legacy_events,
            "verified_events": verified_events,
            "first_invalid_id": None,
            "reason": "checkpoint_last_id_mismatch",
        }
    if state["last_event_hash"] != previous_hash:
        return {
            "ok": False,
            "legacy_events": legacy_events,
            "verified_events": verified_events,
            "first_invalid_id": None,
            "reason": "checkpoint_head_mismatch",
        }

    expected_state_hash = _audit_state_hash(
        int(state["event_count"]),
        int(state["last_event_id"]),
        state["last_event_hash"],
        state["updated_at"],
    )
    if not hmac.compare_digest(state["state_hash"], expected_state_hash):
        return {
            "ok": False,
            "legacy_events": legacy_events,
            "verified_events": verified_events,
            "first_invalid_id": None,
            "reason": "checkpoint_hash_mismatch",
        }

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
