from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
import re
import socket
from contextlib import asynccontextmanager
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status

from .capability_gate import CapabilityGate, GateState
from .db import get_conn, init_db
from .schemas import (
    KnowledgeCreate,
    KnowledgeItem,
    KnowledgeUpdate,
    Sensitivity,
    SourceType,
    Status,
    TransformationState,
)

_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*\S{6,}", re.IGNORECASE),
    re.compile(r"\b(?:token|api[_-]?key|secret)\s*[:=]\s*\S{8,}", re.IGNORECASE),
)

_PROMPT_INJECTION_PATTERNS = (
    re.compile(r"ignore (?:all|previous) instructions", re.IGNORECASE),
    re.compile(r"reveal .*?(?:secret|password|token|key)", re.IGNORECASE),
    re.compile(r"system prompt", re.IGNORECASE),
)

_DERIVED_SOURCE_TYPES: set[SourceType] = {"audio_transcript", "ocr_text", "translation"}
_MAX_EXTERNAL_RESPONSE_BYTES = 65_536
_MIN_API_TOKEN_LENGTH = 32


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _contains_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in _SECRET_PATTERNS)


def _redact_secrets(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED:SENSITIVE]", redacted)
    return redacted


def _contains_prompt_injection(value: str) -> bool:
    return any(pattern.search(value) for pattern in _PROMPT_INJECTION_PATTERNS)


def _provenance_hash(
    title: str,
    content: str,
    source_type: SourceType,
    purpose: str,
    sensitivity: Sensitivity,
    transformation_state: TransformationState,
) -> str:
    material = "\n".join(
        [title, content, source_type, purpose, sensitivity, transformation_state]
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _guard_input(
    *,
    title: str,
    content: str,
    source_type: SourceType,
    purpose: str,
    sensitivity: Sensitivity,
    transformation_state: TransformationState,
) -> str:
    combined = f"{title}\n{content}"

    if _contains_secret(combined):
        raise HTTPException(
            status_code=422,
            detail="Sensitive secret detected. The value was not stored.",
        )

    if sensitivity in {"sensitive", "restricted"}:
        raise HTTPException(
            status_code=403,
            detail="Sensitive/restricted content is blocked from the pre-pilot knowledge path.",
        )

    if _contains_prompt_injection(combined):
        raise HTTPException(
            status_code=422,
            detail="Untrusted instruction content is blocked from the normal knowledge path.",
        )

    if source_type in _DERIVED_SOURCE_TYPES and transformation_state != "verified_against_original":
        raise HTTPException(
            status_code=422,
            detail="Derived input requires verification against the original source before storage.",
        )

    return _provenance_hash(
        title,
        content,
        source_type,
        purpose,
        sensitivity,
        transformation_state,
    )


def _safe_item(row: Any) -> KnowledgeItem:
    data = dict(row)
    data["title"] = _redact_secrets(data["title"])
    data["content"] = _redact_secrets(data["content"])
    return KnowledgeItem(**data)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ASA/AOIP Knowledge Hub",
    version="0.1.0",
    description="Governed knowledge-management MVP. Not a production deployment.",
    lifespan=lifespan,
)


def _env_flag(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def require_api_auth(authorization: str | None = Header(default=None)) -> None:
    """Require an environment-backed bearer token for all pre-pilot API routes."""
    expected = os.getenv("ASA_API_BEARER_TOKEN", "")
    if len(expected) < _MIN_API_TOKEN_LENGTH:
        raise HTTPException(
            status_code=503,
            detail="API authentication is not securely configured",
        )

    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    supplied = authorization[len(prefix) :].strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credential",
            headers={"WWW-Authenticate": "Bearer"},
        )


def local_runtime_gate() -> CapabilityGate:
    """Build the pre-pilot gate from explicit runtime controls."""
    return CapabilityGate(
        available=_env_flag("ASA_GATE_AVAILABLE"),
        eligible=_env_flag("ASA_GATE_ELIGIBLE"),
        authorized=_env_flag("ASA_GATE_AUTHORIZED"),
        connected=_env_flag("ASA_GATE_CONNECTED"),
        executed=_env_flag("ASA_GATE_EXECUTED"),
        tested=_env_flag("ASA_GATE_TESTED"),
        evidenced=_env_flag("ASA_GATE_EVIDENCED"),
    )


def _external_timeout() -> float:
    raw = os.getenv("ASA_EXTERNAL_TIMEOUT_SECONDS", "3")
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid external timeout configuration") from exc
    if not 1 <= timeout <= 10:
        raise HTTPException(status_code=503, detail="External timeout must be between 1 and 10 seconds")
    return timeout


def _allowed_external_hosts() -> set[str]:
    return {
        item.strip().lower().rstrip(".")
        for item in os.getenv("ASA_EXTERNAL_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    }


def _validate_external_target(raw_url: str) -> tuple[str, str]:
    if not _env_flag("ASA_PRODUCTION_MODE", default=False):
        raise HTTPException(status_code=503, detail="Production mode is not enabled")
    if not _env_flag("ASA_PRODUCTION_APPROVED", default=False):
        raise HTTPException(status_code=503, detail="Production approval gate is closed")
    if not _env_flag("ASA_EXTERNAL_ENABLED", default=False):
        raise HTTPException(status_code=503, detail="External connection is disabled")

    parsed = urlsplit(raw_url)
    if parsed.scheme.lower() != "https":
        raise HTTPException(status_code=503, detail="External target must use HTTPS")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=503, detail="Credentials are forbidden in external URLs")
    if not parsed.hostname:
        raise HTTPException(status_code=503, detail="External target host is missing")

    host = parsed.hostname.lower().rstrip(".")
    if host not in _allowed_external_hosts():
        raise HTTPException(status_code=503, detail="External target host is not allowlisted")

    try:
        addresses = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(status_code=503, detail="External target DNS resolution failed") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise HTTPException(status_code=503, detail="External target resolved to a blocked address")

    return raw_url, host


def _external_probe() -> dict[str, str | int]:
    gate_state = local_runtime_gate().evaluate()
    if gate_state is not GateState.OPERATIONAL:
        raise HTTPException(status_code=503, detail=f"Capability gate: {gate_state.value}")

    raw_url = os.getenv("ASA_EXTERNAL_URL", "").strip()
    if not raw_url:
        raise HTTPException(status_code=503, detail="External target is not configured")
    target, host = _validate_external_target(raw_url)

    request = Request(
        target,
        method="GET",
        headers={
            "User-Agent": "ASA-AOIP-Production-Probe/1.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    opener = build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=_external_timeout()) as response:
            body = response.read(_MAX_EXTERNAL_RESPONSE_BYTES + 1)
            if len(body) > _MAX_EXTERNAL_RESPONSE_BYTES:
                raise HTTPException(status_code=502, detail="External response exceeded size limit")
            status_code = int(response.status)
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"External target returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise HTTPException(status_code=502, detail="External target connection failed") from exc

    if not 200 <= status_code < 300:
        raise HTTPException(status_code=502, detail=f"External target returned HTTP {status_code}")

    return {"status": "ok", "host": host, "http_status": status_code}


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

    gate_state = local_runtime_gate().evaluate()
    if gate_state is not GateState.OPERATIONAL:
        raise HTTPException(status_code=503, detail=f"Capability gate: {gate_state.value}")

    return {
        "status": "ok",
        "service": "asa-aoip-knowledge-hub",
        "database": "ok",
        "capability_gate": gate_state.value,
    }


@app.get("/api/v1/external/health", dependencies=[Depends(require_api_auth)])
def external_health() -> dict[str, str | int]:
    """Probe one explicitly approved HTTPS endpoint under fail-closed controls."""
    return _external_probe()


@app.post(
    "/api/v1/knowledge",
    response_model=KnowledgeItem,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_auth)],
)
def create_knowledge(payload: KnowledgeCreate) -> KnowledgeItem:
    provenance_hash = _guard_input(
        title=payload.title,
        content=payload.content,
        source_type=payload.source_type,
        purpose=payload.purpose,
        sensitivity=payload.sensitivity,
        transformation_state=payload.transformation_state,
    )

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO knowledge_items (
                title, content, status, source_type, purpose,
                sensitivity, transformation_state, provenance_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                payload.content,
                payload.status,
                payload.source_type,
                payload.purpose,
                payload.sensitivity,
                payload.transformation_state,
                provenance_hash,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM knowledge_items WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return _safe_item(row)


@app.get(
    "/api/v1/knowledge",
    response_model=list[KnowledgeItem],
    dependencies=[Depends(require_api_auth)],
)
def list_knowledge(
    q: str | None = Query(default=None, max_length=200),
    status_filter: Status | None = Query(default=None, alias="status"),
) -> list[KnowledgeItem]:
    sql = "SELECT * FROM knowledge_items WHERE 1=1"
    params: list[str] = []
    if q:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term])
    if status_filter:
        sql += " AND status = ?"
        params.append(status_filter)
    sql += " ORDER BY id DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_safe_item(row) for row in rows]


@app.get(
    "/api/v1/knowledge/{item_id}",
    response_model=KnowledgeItem,
    dependencies=[Depends(require_api_auth)],
)
def get_knowledge(item_id: int) -> KnowledgeItem:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM knowledge_items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return _safe_item(row)


@app.patch(
    "/api/v1/knowledge/{item_id}",
    response_model=KnowledgeItem,
    dependencies=[Depends(require_api_auth)],
)
def update_knowledge(item_id: int, payload: KnowledgeUpdate) -> KnowledgeItem:
    if all(
        value is None
        for value in (
            payload.title,
            payload.content,
            payload.status,
            payload.source_type,
            payload.purpose,
            payload.sensitivity,
            payload.transformation_state,
        )
    ):
        raise HTTPException(status_code=400, detail="No changes supplied")

    with get_conn() as conn:
        current = conn.execute(
            "SELECT * FROM knowledge_items WHERE id = ?", (item_id,)
        ).fetchone()
        if current is None:
            raise HTTPException(status_code=404, detail="Knowledge item not found")

        merged = dict(current)
        for field in (
            "title",
            "content",
            "status",
            "source_type",
            "purpose",
            "sensitivity",
            "transformation_state",
        ):
            value = getattr(payload, field)
            if value is not None:
                merged[field] = value

        provenance_hash = _guard_input(
            title=merged["title"],
            content=merged["content"],
            source_type=merged["source_type"],
            purpose=merged["purpose"],
            sensitivity=merged["sensitivity"],
            transformation_state=merged["transformation_state"],
        )

        conn.execute(
            """
            UPDATE knowledge_items
            SET title = ?,
                content = ?,
                status = ?,
                source_type = ?,
                purpose = ?,
                sensitivity = ?,
                transformation_state = ?,
                provenance_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                merged["title"],
                merged["content"],
                merged["status"],
                merged["source_type"],
                merged["purpose"],
                merged["sensitivity"],
                merged["transformation_state"],
                provenance_hash,
                item_id,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM knowledge_items WHERE id = ?", (item_id,)).fetchone()
    return _safe_item(row)


@app.delete(
    "/api/v1/knowledge/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_api_auth)],
)
def delete_knowledge(item_id: int) -> Response:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM knowledge_items WHERE id = ?", (item_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
