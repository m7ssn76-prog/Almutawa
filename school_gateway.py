#!/usr/bin/env python3
"""External HTTPS gateway smoke test for Smart Education System.

Safety boundary:
- Sends synthetic data only in live smoke mode.
- Does not connect to or claim integration with a real school system.
- Production school integration requires an authorized API endpoint, credentials, RBAC, privacy/retention rules, and school approval.
"""
from __future__ import annotations

import json
import os
import sys
from urllib import request, error

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


def post_json(url: str, payload: dict, timeout: int = 15) -> dict:
    if payload.get("contains_real_child_data") is not False or payload.get("synthetic") is not True:
        raise ValueError("Live smoke mode permits synthetic data only")
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "smart-education-gateway/1.0"},
    )
    with request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return {"status": response.status, "body": json.loads(raw)}


def live_smoke() -> dict:
    url = os.environ.get("SCHOOL_GATEWAY_SMOKE_URL", DEFAULT_SMOKE_URL)
    result = post_json(url, build_synthetic_payload())
    if result["status"] < 200 or result["status"] >= 300:
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
    ]
    return {"passed": sum(checks), "total": len(checks), "all_passed": all(checks)}


if __name__ == "__main__":
    if "--live-smoke" in sys.argv:
        try:
            print(json.dumps(live_smoke(), indent=2))
        except (error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"external_https_connection": False, "error": str(exc)}, indent=2))
            raise SystemExit(1)
    else:
        print(json.dumps({"name": "School Gateway", "tests": self_test()}, indent=2))
