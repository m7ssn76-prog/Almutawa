#!/usr/bin/env python3
"""External HTTPS gateway smoke test for Smart Education System.

Safety boundary:
- Sends synthetic data only in live smoke mode.
- Does not connect to or claim integration with a real school system.
- Production school integration requires an authorized API endpoint, credentials, RBAC, privacy/retention rules, and school approval.
"""
from __future__ import annotations

import http.client
import json
import os
import ssl
import sys
from urllib.parse import urlsplit

DEFAULT_SMOKE_URL = "https://postman-echo.com/post"


def build_synthetic_payload() -> dict:
    return {
        "schema": "smart-education-connection-smoke-v1",
        "synthetic": True,
        "student_id": "SYNTHETIC-001",
        "event_type": "connectivity_test",
        "contains_real_child_data": False,
        "message": "Synthetic connectivity check only",
    }


def _validate_https_url(url: str) -> tuple[str, int, str]:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise ValueError("HTTPS is required")
    if not parsed.hostname:
        raise ValueError("Endpoint hostname is required")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in URL are forbidden")
    port = parsed.port or 443
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return parsed.hostname, port, path


def post_json(url: str, payload: dict, timeout: int = 15) -> dict:
    if payload.get("contains_real_child_data") is not False or payload.get("synthetic") is not True:
        raise ValueError("Live smoke mode permits synthetic data only")

    host, port, path = _validate_https_url(url)
    body = json.dumps(payload).encode("utf-8")
    context = ssl.create_default_context()
    connection = http.client.HTTPSConnection(host, port=port, timeout=timeout, context=context)
    try:
        connection.request(
            "POST",
            path,
            body=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "smart-education-gateway/1.1",
            },
        )
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        return {"status": response.status, "body": json.loads(raw)}
    finally:
        connection.close()


def live_smoke() -> dict:
    url = os.environ.get("SCHOOL_GATEWAY_SMOKE_URL", DEFAULT_SMOKE_URL)
    result = post_json(url, build_synthetic_payload())
    if not 200 <= result["status"] < 300:
        raise RuntimeError(f"Unexpected HTTP status: {result['status']}")
    return {
        "external_https_connection": True,
        "endpoint_type": "public_test_echo",
        "synthetic_data_only": True,
        "http_status": result["status"],
        "real_school_system_connected": False,
    }


def self_test() -> dict:
    payload = build_synthetic_payload()
    checks = [
        payload["synthetic"] is True,
        payload["contains_real_child_data"] is False,
        payload["student_id"].startswith("SYNTHETIC-"),
        _validate_https_url(DEFAULT_SMOKE_URL)[0] == "postman-echo.com",
    ]
    return {"passed": sum(checks), "total": len(checks), "all_passed": all(checks)}


if __name__ == "__main__":
    if "--live-smoke" in sys.argv:
        try:
            print(json.dumps(live_smoke(), indent=2))
        except (OSError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"external_https_connection": False, "error": str(exc)}, indent=2))
            raise SystemExit(1)
    else:
        print(json.dumps({"name": "School Gateway", "tests": self_test()}, indent=2))
