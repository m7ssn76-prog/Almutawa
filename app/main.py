from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Response, status

from .db import get_conn, init_db
from .schemas import KnowledgeCreate, KnowledgeItem, KnowledgeUpdate, Status


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


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "service": "asa-aoip-knowledge-hub", "database": "ok"}


@app.post("/api/v1/knowledge", response_model=KnowledgeItem, status_code=status.HTTP_201_CREATED)
def create_knowledge(payload: KnowledgeCreate) -> KnowledgeItem:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO knowledge_items (title, content, status) VALUES (?, ?, ?)",
            (payload.title, payload.content, payload.status),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM knowledge_items WHERE id = ?", (cur.lastrowid,)).fetchone()
    return KnowledgeItem(**dict(row))


@app.get("/api/v1/knowledge", response_model=list[KnowledgeItem])
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
    return [KnowledgeItem(**dict(row)) for row in rows]


@app.get("/api/v1/knowledge/{item_id}", response_model=KnowledgeItem)
def get_knowledge(item_id: int) -> KnowledgeItem:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM knowledge_items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return KnowledgeItem(**dict(row))


@app.patch("/api/v1/knowledge/{item_id}", response_model=KnowledgeItem)
def update_knowledge(item_id: int, payload: KnowledgeUpdate) -> KnowledgeItem:
    if payload.title is None and payload.content is None and payload.status is None:
        raise HTTPException(status_code=400, detail="No changes supplied")

    with get_conn() as conn:
        exists = conn.execute("SELECT id FROM knowledge_items WHERE id = ?", (item_id,)).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Knowledge item not found")

        conn.execute(
            """
            UPDATE knowledge_items
            SET title = COALESCE(?, title),
                content = COALESCE(?, content),
                status = COALESCE(?, status),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (payload.title, payload.content, payload.status, item_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM knowledge_items WHERE id = ?", (item_id,)).fetchone()
    return KnowledgeItem(**dict(row))


@app.delete(
    "/api/v1/knowledge/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_knowledge(item_id: int) -> Response:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM knowledge_items WHERE id = ?", (item_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
