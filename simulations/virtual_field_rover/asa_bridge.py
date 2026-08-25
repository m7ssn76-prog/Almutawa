from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_API = "http://127.0.0.1:8000"
TITLE = "Digital Farm Synthetic Monitoring Run"


def build_knowledge_payload(summary: dict) -> dict:
    if summary.get("simulation_only") is not True:
        raise ValueError("Bridge accepts simulation-only summaries")
    if summary.get("real_farm_connected") is not False:
        raise ValueError("Real-farm connection must remain false")
    if summary.get("classification") != "Internal Test Only":
        raise ValueError("Unexpected evidence classification")
    if not summary.get("evidence_chain", {}).get("valid"):
        raise ValueError("Environmental evidence chain is invalid")
    if not summary.get("asa_aoip_gateway", {}).get("valid"):
        raise ValueError("ASA/AOIP gateway chain is invalid")
    if summary.get("asa_aoip_gateway", {}).get("external_connection") is not False:
        raise ValueError("External connection must remain false")

    safe_content = {
        "schema": "asa.aoip.digital-farm-run-summary.v1",
        "classification": "Internal Test Only",
        "simulation_only": True,
        "real_farm_connected": False,
        "cycles": int(summary.get("cycles", 0)),
        "privacy_yields": int(summary.get("privacy_yields", 0)),
        "false_alerts": int(summary.get("false_alerts", 0)),
        "evidence_chain": summary.get("evidence_chain", {}),
        "asa_aoip_gateway": summary.get("asa_aoip_gateway", {}),
        "last_state": summary.get("last_state"),
        "boundary": {
            "physical_actuation": False,
            "person_tracking": False,
            "facial_recognition": False,
            "external_connection": False,
        },
    }
    return {
        "title": TITLE,
        "content": json.dumps(safe_content, ensure_ascii=False, sort_keys=True),
        "status": "draft",
        "source_type": "text",
        "purpose": "synthetic_environmental_monitoring",
        "sensitivity": "public",
        "transformation_state": "original",
        "data_origin": "synthetic",
        "approval_reference": None,
    }


def post_payload(payload: dict, api_base: str, token: str, timeout: float = 10.0) -> dict:
    if len(token) < 32:
        raise ValueError("ASA_API_BEARER_TOKEN must be at least 32 characters")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        api_base.rstrip("/") + "/api/v1/knowledge",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as response:
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
