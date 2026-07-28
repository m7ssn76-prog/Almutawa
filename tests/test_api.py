from pathlib import Path

from fastapi.testclient import TestClient

from app import db
from app.main import app


def setup_module() -> None:
    db.DB_PATH = Path("test_asa_aoip.db")
    if db.DB_PATH.exists():
        db.DB_PATH.unlink()
    db.init_db()


def teardown_module() -> None:
    if db.DB_PATH.exists():
        db.DB_PATH.unlink()


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_knowledge_crud() -> None:
    created = client.post(
        "/api/v1/knowledge",
        json={"title": "Welding lesson", "content": "Documented cladding lesson", "status": "reviewed"},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    fetched = client.get(f"/api/v1/knowledge/{item_id}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Welding lesson"

    updated = client.patch(f"/api/v1/knowledge/{item_id}", json={"status": "approved"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "approved"

    deleted = client.delete(f"/api/v1/knowledge/{item_id}")
    assert deleted.status_code == 204


def test_search_and_validation() -> None:
    client.post("/api/v1/knowledge", json={"title": "Safety note", "content": "PPE and inspection"})
    client.post(
        "/api/v1/knowledge",
        json={"title": "Quality note", "content": "WPS compliance", "status": "reviewed"},
    )

    result = client.get("/api/v1/knowledge", params={"q": "WPS", "status": "reviewed"})
    assert result.status_code == 200
    assert len(result.json()) == 1

    invalid = client.post("/api/v1/knowledge", json={"title": "x", "content": ""})
    assert invalid.status_code == 422
