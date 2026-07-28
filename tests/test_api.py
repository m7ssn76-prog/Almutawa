from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    database_path = tmp_path / "test_asa_aoip.db"
    monkeypatch.setattr(db, "DB_PATH", database_path)
    db.init_db()

    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "asa-aoip-knowledge-hub",
        "database": "ok",
    }


def test_knowledge_crud(client: TestClient) -> None:
    created = client.post(
        "/api/v1/knowledge",
        json={
            "title": "Welding lesson",
            "content": "Documented cladding lesson",
            "status": "reviewed",
        },
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    fetched = client.get(f"/api/v1/knowledge/{item_id}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Welding lesson"

    updated = client.patch(
        f"/api/v1/knowledge/{item_id}",
        json={"status": "approved"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "approved"

    deleted = client.delete(f"/api/v1/knowledge/{item_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/knowledge/{item_id}")
    assert missing.status_code == 404


def test_search_and_validation(client: TestClient) -> None:
    first = client.post(
        "/api/v1/knowledge",
        json={"title": "Safety note", "content": "PPE and inspection"},
    )
    second = client.post(
        "/api/v1/knowledge",
        json={
            "title": "Quality note",
            "content": "WPS compliance",
            "status": "reviewed",
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201

    result = client.get(
        "/api/v1/knowledge",
        params={"q": "WPS", "status": "reviewed"},
    )
    assert result.status_code == 200
    assert len(result.json()) == 1

    invalid = client.post(
        "/api/v1/knowledge",
        json={"title": "x", "content": ""},
    )
    assert invalid.status_code == 422
