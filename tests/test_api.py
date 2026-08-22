from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import db
from app.capability_gate import CapabilityGate
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
        "capability_gate": "Operational",
    }


def test_health_blocks_when_capability_gate_fails(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.local_runtime_gate",
        lambda: CapabilityGate(
            available=True,
            eligible=True,
            authorized=False,
            connected=False,
            executed=False,
            tested=False,
            evidenced=False,
        ),
    )

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "Capability gate: Authorized"


def test_knowledge_crud(client: TestClient) -> None:
    created = client.post(
        "/api/v1/knowledge",
        json={
            "title": "Welding lesson",
            "content": "Synthetic pre-pilot lesson",
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
        json={"status": "archived"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "archived"

    deleted = client.delete(f"/api/v1/knowledge/{item_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/knowledge/{item_id}")
    assert missing.status_code == 404


def test_search_and_validation(client: TestClient) -> None:
    first = client.post(
        "/api/v1/knowledge",
        json={"title": "Safety note", "content": "Synthetic inspection example"},
    )
    second = client.post(
        "/api/v1/knowledge",
        json={
            "title": "Quality note",
            "content": "Synthetic procedure example",
            "status": "reviewed",
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201

    result = client.get(
        "/api/v1/knowledge",
        params={"q": "procedure", "status": "reviewed"},
    )
    assert result.status_code == 200
    assert len(result.json()) == 1

    invalid = client.post(
        "/api/v1/knowledge",
        json={"title": "x", "content": ""},
    )
    assert invalid.status_code == 422


def test_approved_status_is_blocked_in_pre_pilot(client: TestClient) -> None:
    response = client.post(
        "/api/v1/knowledge",
        json={
            "title": "Approval boundary",
            "content": "Synthetic test",
            "status": "approved",
        },
    )
    assert response.status_code == 422
