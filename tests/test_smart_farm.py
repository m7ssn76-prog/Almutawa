from __future__ import annotations

from fastapi.testclient import TestClient

from app.smart_farm import app

_TOKEN = "t" * 40
_AUTH = {"Authorization": f"Bearer {_TOKEN}"}


def _payload(**overrides):
    payload = {
        "temperature_c": 28.0,
        "humidity_pct": 55.0,
        "soil_moisture_pct": 48.0,
        "battery_pct": 80.0,
        "connectivity": "online",
        "data_origin": "synthetic",
    }
    payload.update(overrides)
    return payload


def test_health_is_monitor_only(monkeypatch):
    monkeypatch.delenv("SMART_FARM_OPENAI_ENABLED", raising=False)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "asa-smart-farm-ai"
    assert body["control_mode"] == "monitor_only"
    assert body["external_actuation"] is False
    assert body["ai_enabled"] is False


def test_observe_requires_auth(monkeypatch):
    monkeypatch.setenv("ASA_API_BEARER_TOKEN", _TOKEN)
    with TestClient(app) as client:
        response = client.post("/api/v1/farm/observe", json=_payload())
    assert response.status_code == 401


def test_observe_normal_is_local_and_non_actuating(monkeypatch):
    monkeypatch.setenv("ASA_API_BEARER_TOKEN", _TOKEN)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/farm/observe",
            headers=_AUTH,
            json=_payload(),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "normal"
    assert body["recommended_data_mode"] == "live"
    assert body["control_mode"] == "monitor_only"
    assert body["external_actuation"] is False
    assert body["telemetry_storage"] == "not_implemented"


def test_offline_and_low_battery_escalate_to_attention(monkeypatch):
    monkeypatch.setenv("ASA_API_BEARER_TOKEN", _TOKEN)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/farm/observe",
            headers=_AUTH,
            json=_payload(connectivity="offline", battery_pct=10.0),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "attention"
    assert "connectivity_offline" in body["alerts"]
    assert "battery_critical_for_monitoring" in body["alerts"]
    assert body["recommended_data_mode"] == "buffer_locally_then_sync"
    assert body["external_actuation"] is False


def test_custom_policy_is_supported(monkeypatch):
    monkeypatch.setenv("ASA_API_BEARER_TOKEN", _TOKEN)
    payload = _payload(
        temperature_c=30.0,
        policy={
            "temperature_min_c": 10.0,
            "temperature_max_c": 29.0,
            "humidity_min_pct": 20.0,
            "humidity_max_pct": 90.0,
            "soil_moisture_min_pct": 20.0,
            "soil_moisture_max_pct": 85.0,
            "battery_watch_pct": 35.0,
            "battery_attention_pct": 15.0,
        },
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/farm/observe",
            headers=_AUTH,
            json=payload,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "watch"
    assert "temperature_outside_selected_range" in body["alerts"]


def test_invalid_policy_fails_validation(monkeypatch):
    monkeypatch.setenv("ASA_API_BEARER_TOKEN", _TOKEN)
    payload = _payload(
        policy={
            "temperature_min_c": 45.0,
            "temperature_max_c": 20.0,
        }
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/farm/observe",
            headers=_AUTH,
            json=payload,
        )
    assert response.status_code == 422


def test_ai_path_is_fail_closed_by_default(monkeypatch):
    monkeypatch.setenv("ASA_API_BEARER_TOKEN", _TOKEN)
    monkeypatch.delenv("SMART_FARM_OPENAI_ENABLED", raising=False)
    for name in (
        "ASA_GATE_AVAILABLE",
        "ASA_GATE_ELIGIBLE",
        "ASA_GATE_AUTHORIZED",
        "ASA_GATE_CONNECTED",
        "ASA_GATE_EXECUTED",
        "ASA_GATE_TESTED",
        "ASA_GATE_EVIDENCED",
    ):
        monkeypatch.setenv(name, "true")
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/farm/ai-assess",
            headers=_AUTH,
            json=_payload(),
        )
    assert response.status_code == 503
    assert response.json()["detail"] == "Smart Farm OpenAI path is disabled"
