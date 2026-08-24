#!/usr/bin/env python3
"""External HTTPS gateway for Smart Education System.

Safety boundary:
- Synthetic write-smoke sends synthetic data only.
- Official Ministry of Education smoke test verifies the public Noor integration metadata surface only.
- No real child/student records are sent or fetched.
- Operational school integration still requires the school's authorized API endpoint, credentials, RBAC, privacy/retention rules, and technical approval.
"""
from __future__ import annotations

import http.client
import json
import os
import ssl
import sys
from urllib.parse import urlsplit

DEFAULT_SMOKE_URL = "https://postman-echo.com/post"
OFFICIAL_MOE_INTEGRATION_METADATA_URL = (
    "https://mip.moe.gov.sa/noor/FederationMetadata/2007-06/FederationMetadata.xml"
)
OFFICIAL_MOE_HOST = "mip.moe.gov.sa"


def build_synthetic_payload() -> dict:
    return {
        "schema": "smart-education-connection-smoke-v1",
        "synthetic": True,
        "student_id": "SYNTHETIC-001",
        "event_type": "connectivity_test",
        "contains_real_child_data": False,
        "message": "Synthetic connectivity check only",
    }


def _validate_https_url(url: str, allowed_hosts: set[str] | None = None) -> tuple[str, int, str]:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise ValueError("HTTPS is required")
    if not parsed.hostname:
        raise ValueError("Endpoint hostname is required")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in URL are forbidden")
    if allowed_hosts is not None and parsed.hostname not in allowed_hosts:
        raise ValueError("Endpoint host is not allow-listed")
    port = parsed.port or 443
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return parsed.hostname, port, path


def _https_connection(host: str, port: int, timeout: int) -> http.client.HTTPSConnection:
    return http.client.HTTPSConnection(
        host,
        port=port,
        timeout=timeout,
        context=ssl.create_default_context(),
    )


def post_json(url: str, payload: dict, timeout: int = 15) -> dict:
    if payload.get("contains_real_child_data") is not False or payload.get("synthetic") is not True:
        raise ValueError("Live smoke mode permits synthetic data only")

    host, port, path = _validate_https_url(url)
    body = json.dumps(payload).encode("utf-8")
    connection = _https_connection(host, port, timeout)
    try:
        connection.request(
            "POST",
            path,
            body=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "smart-education-gateway/1.3",
            },
        )
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        return {"status": response.status, "body": json.loads(raw)}
    finally:
        connection.close()


def get_public_resource(url: str, allowed_hosts: set[str], timeout: int = 15) -> dict:
    host, port, path = _validate_https_url(url, allowed_hosts=allowed_hosts)
    connection = _https_connection(host, port, timeout)
    try:
        connection.request(
            "GET",
            path,
            headers={
                "Accept": "application/xml,text/xml,text/plain,*/*",
                "User-Agent": "smart-education-gateway/1.3",
            },
        )
        response = connection.getresponse()
        sample = response.read(8192)
        return {
            "status": response.status,
            "content_type": response.getheader("Content-Type") or "",
            "sample": sample,
        }
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


def official_moe_integration_smoke() -> dict:
    result = get_public_resource(
        OFFICIAL_MOE_INTEGRATION_METADATA_URL,
        allowed_hosts={OFFICIAL_MOE_HOST},
    )
    if not 200 <= result["status"] < 300:
        raise RuntimeError(f"MOE integration metadata returned HTTP {result['status']}")
    sample = result["sample"].lstrip()
    if not sample:
        raise RuntimeError("MOE integration metadata returned an empty response")
    xml_like = sample.startswith(b"<") and (
        b"EntityDescriptor" in sample or b"FederationMetadata" in sample or b"RoleDescriptor" in sample
    )
    if not xml_like:
        raise RuntimeError("MOE integration endpoint did not return expected federation metadata")
    return {
        "official_moe_integration_surface_connected": True,
        "source_host": OFFICIAL_MOE_HOST,
        "http_status": result["status"],
        "metadata_verified": True,
        "contains_real_child_records": False,
        "operational_school_api_connected": False,
    }


def configured_school_api_status() -> dict:
    endpoint = os.environ.get("SCHOOL_API_ENDPOINT")
    token_present = bool(os.environ.get("SCHOOL_API_BEARER_TOKEN"))
    return {
        "configured": bool(endpoint),
        "credential_present": token_present,
        "ready_for_authorized_operational_probe": bool(endpoint and token_present),
    }


def self_test() -> dict:
    payload = build_synthetic_payload()
    checks = [
        payload["synthetic"] is True,
        payload["contains_real_child_data"] is False,
        payload["student_id"].startswith("SYNTHETIC-"),
        _validate_https_url(DEFAULT_SMOKE_URL)[0] == "postman-echo.com",
        _validate_https_url(OFFICIAL_MOE_INTEGRATION_METADATA_URL, {OFFICIAL_MOE_HOST})[0] == OFFICIAL_MOE_HOST,
    ]
    return {"passed": sum(checks), "total": len(checks), "all_passed": all(checks)}


if __name__ == "__main__":
    try:
        if "--live-smoke" in sys.argv:
            print(json.dumps(live_smoke(), indent=2))
        elif "--official-moe-smoke" in sys.argv:
            print(json.dumps(official_moe_integration_smoke(), indent=2))
        elif "--school-api-status" in sys.argv:
            print(json.dumps(configured_school_api_status(), indent=2))
        else:
            print(json.dumps({"name": "School Gateway", "tests": self_test()}, indent=2))
    except (OSError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"connection": False, "error": str(exc)}, indent=2))
        raise SystemExit(1)
