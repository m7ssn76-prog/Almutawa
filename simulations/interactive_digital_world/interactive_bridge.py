from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TITLE = "Interactive Digital World Snapshot"
DEFAULT_API = "http://127.0.0.1:8000"


def build_payload(snapshot: dict) -> dict:
    if snapshot.get("classification") != "Internal Test Only":
        raise ValueError("Unexpected classification")
    if snapshot.get("simulation_only") is not True:
        raise ValueError("Interactive bridge accepts simulation-only state")
    if snapshot.get("real_environment_connected") is not False:
        raise ValueError("Real-environment connection must remain false")
    if snapshot.get("physical_actuation") is not False:
        raise ValueError("Physical actuation must remain disabled")
    if not snapshot.get("evidence_chain", {}).get("valid"):
        raise ValueError("Evidence chain must verify before ingest")

    safe = {
        "schema": snapshot.get("schema"),
        "classification": snapshot.get("classification"),
        "simulation_only": True,
        "real_environment_connected": False,
        "physical_actuation": False,
        "clock_seconds": snapshot.get("clock_seconds"),
        "sequence": snapshot.get("sequence"),
        "world": snapshot.get("world"),
        "rover": snapshot.get("rover"),
        "last_command": snapshot.get("last_command"),
        "last_perception": snapshot.get("last_perception"),
        "evidence_chain": snapshot.get("evidence_chain"),
        "boundary": {
            "person_tracking": False,
            "facial_recognition": False,
            "covert_monitoring": False,
            "real_world_action": False,
        },
    }
    return {
        "title": TITLE,
        "content": json.dumps(safe, ensure_ascii=False, sort_keys=True),
        "status": "draft",
        "source_type": "text",
        "purpose": "interactive_digital_world_internal_test",
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
            if response.status != 201:
                raise RuntimeError(f"Unexpected ASA/AOIP status: {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ASA/AOIP rejected interactive snapshot: HTTP {exc.code} {detail}") from exc
    except URLError as exc:
        raise RuntimeError("ASA/AOIP local API is unavailable") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--api-base", default=os.getenv("ASA_API_BASE", DEFAULT_API))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    payload = build_payload(snapshot)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    result = post_payload(payload, args.api_base, os.getenv("ASA_API_BEARER_TOKEN", ""))
    print(json.dumps({
        "bridge": "PASS",
        "knowledge_id": result.get("id"),
        "provenance_hash": result.get("provenance_hash"),
        "data_origin": result.get("data_origin"),
        "status": result.get("status"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
