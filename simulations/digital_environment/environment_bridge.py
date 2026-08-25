from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_API = "http://127.0.0.1:8000"
TITLE = "Digital Environment Synthetic Monitoring Suite"


def build_knowledge_payload(summary: dict) -> dict:
    if summary.get("classification") != "Internal Test Only":
        raise ValueError("Unexpected classification")
    if summary.get("simulation_only") is not True:
        raise ValueError("Bridge accepts simulation-only evidence")
    if summary.get("real_environment_connected") is not False:
        raise ValueError("Real-environment connection must remain false")
    if summary.get("external_connection") is not False:
        raise ValueError("External connection must remain false")
    if summary.get("all_evidence_valid") is not True:
        raise ValueError("All evidence chains must verify before ingest")

    safe_profiles = []
    for profile in summary.get("profiles", []):
        if profile.get("real_environment_connected") is not False:
            raise ValueError("Profile claims a real-environment connection")
        if not profile.get("evidence_chain", {}).get("valid"):
            raise ValueError("Profile evidence chain is invalid")
        if not profile.get("asa_aoip_gateway", {}).get("valid"):
            raise ValueError("Profile ASA/AOIP gateway chain is invalid")
        safe_profiles.append({
            "environment_id": profile.get("environment_id"),
            "environment_type": profile.get("environment_type"),
            "cycles": int(profile.get("cycles", 0)),
            "false_alerts": int(profile.get("false_alerts", 0)),
            "privacy_yields": int(profile.get("privacy_yields", 0)),
            "privacy_reroutes": int(profile.get("privacy_reroutes", 0)),
            "adaptive_revisits": int(profile.get("adaptive_revisits", 0)),
            "degraded_sensor_cycles": int(profile.get("degraded_sensor_cycles", 0)),
            "evidence_chain": profile.get("evidence_chain", {}),
            "asa_aoip_gateway": profile.get("asa_aoip_gateway", {}),
            "last_state": profile.get("last_state"),
        })

    content = {
        "schema": "asa.aoip.digital-environment-suite.v1",
        "classification": "Internal Test Only",
        "simulation_only": True,
        "real_environment_connected": False,
        "environment_count": len(safe_profiles),
        "environment_types": summary.get("environment_types", []),
        "profiles": safe_profiles,
        "boundary": {
            "physical_actuation": False,
            "person_tracking": False,
            "facial_recognition": False,
            "covert_monitoring": False,
            "external_connection": False,
            "human_verification_required_for_real_world_action": True,
        },
    }
    return {
        "title": TITLE,
        "content": json.dumps(content, ensure_ascii=False, sort_keys=True),
        "status": "draft",
        "source_type": "text",
        "purpose": "synthetic_digital_environment_monitoring",
        "sensitivity": "public",
        "transformation_state": "original",
        "data_origin": "synthetic",
        "approval_reference": None,
    }


def post_payload(payload: dict, api_base: str, token: str, timeout: float = 10.0) -> dict:
    if len(token) < 32:
        raise ValueError("ASA_API_BEARER_TOKEN must be at least 32 characters")
    request = Request(
        api_base.rstrip("/") + "/api/v1/knowledge",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
            if response.status != 201:
                raise RuntimeError(f"Unexpected ASA/AOIP status: {response.status}")
            return result
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ASA/AOIP bridge rejected evidence: HTTP {exc.code} {detail}") from exc
    except URLError as exc:
        raise RuntimeError("ASA/AOIP local API is unavailable") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path)
    parser.add_argument("--api-base", default=os.getenv("ASA_API_BASE", DEFAULT_API))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    payload = build_knowledge_payload(summary)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    token = os.getenv("ASA_API_BEARER_TOKEN", "")
    result = post_payload(payload, args.api_base, token)
    print(json.dumps({
        "bridge": "PASS",
        "knowledge_id": result.get("id"),
        "provenance_hash": result.get("provenance_hash"),
        "data_origin": result.get("data_origin"),
        "status": result.get("status"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
