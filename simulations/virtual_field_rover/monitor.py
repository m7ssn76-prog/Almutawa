from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent


@dataclass
class Reading:
    name: str
    value: float
    health: float
    valid: bool
    anomaly_score: float


class EvidenceChain:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.previous = "0" * 64

    @staticmethod
    def canonical(value: dict) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

    def append(self, event_type: str, payload: dict) -> dict:
        record = {
            "event_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "event_type": event_type,
            "classification": "Internal Test Only",
            "source_type": "synthetic_virtual_farm",
            "payload": payload,
            "previous_hash": self.previous,
        }
        record_hash = hashlib.sha256(self.canonical(record)).hexdigest()
        record["record_hash"] = record_hash
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.previous = record_hash
        return record

    def verify(self) -> tuple[bool, int]:
        if not self.path.exists():
            return True, 0
        previous = "0" * 64
        count = 0
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            claimed = item.pop("record_hash")
            if item["previous_hash"] != previous:
                return False, count
            actual = hashlib.sha256(self.canonical(item)).hexdigest()
            if actual != claimed:
                return False, count
            previous = claimed
            count += 1
        return True, count


class DigitalFarm:
    def __init__(self, path: Path, seed: int):
        self.cfg = json.loads(path.read_text(encoding="utf-8"))
        self.rng = random.Random(seed)
        self.index = 0
        self.incident_remaining = 0
        self.incident_id: str | None = None

    def zone_at(self, x: int, y: int) -> dict | None:
        for zone in self.cfg["zones"]:
            if zone["x1"] <= x <= zone["x2"] and zone["y1"] <= y <= zone["y2"]:
                return zone
        return None

    def next_context(self) -> tuple[dict, bool]:
        point = self.cfg["patrol_waypoints"][self.index % len(self.cfg["patrol_waypoints"])]
        self.index += 1
        zone = self.zone_at(point["x"], point["y"])
        if zone is None:
            raise RuntimeError("waypoint outside geofence")

        if self.incident_remaining <= 0 and self.rng.random() < 0.035:
            self.incident_remaining = self.rng.randint(4, 8)
            self.incident_id = f"SIM-{uuid.uuid4().hex[:10]}"
        incident = self.incident_remaining > 0
        if incident:
            self.incident_remaining -= 1
        else:
            self.incident_id = None

        human_presence = zone["type"] == "open_privacy_safe" and self.rng.random() < 0.20
        public_context = {
            "farm_id": self.cfg["farm_id"],
            "zone_id": zone["id"],
            "zone_type": zone["type"],
            "position": point,
        }
        hidden = {"incident": incident, "incident_id": self.incident_id, "human_presence": human_presence}
        return public_context | {"_hidden": hidden}, incident


class RobustAnomalyEngine:
    def __init__(self, warmup: int = 18, window: int = 40):
        self.warmup = warmup
        self.history = defaultdict(lambda: deque(maxlen=window))

    def score(self, name: str, value: float, health: float, valid: bool) -> float:
        if not valid or health <= 0:
            return 0.0
        values = self.history[name]
        if len(values) < self.warmup:
            values.append(value)
            return 0.0
        median = statistics.median(values)
        deviations = [abs(v - median) for v in values]
        mad = max(statistics.median(deviations), 0.25)
        robust_z = abs(value - median) / (1.4826 * mad)
        score = min(1.0, robust_z / 5.0) * health
        if score < 0.55:
            values.append(value)
        return round(score, 6)

    @staticmethod
    def fuse(scores: dict[str, float], health: dict[str, float]) -> float:
        total = sum(max(0.0, min(1.0, health[k])) for k in scores)
        if total == 0:
            return 0.0
        weighted = sum(scores[k] * health[k] for k in scores) / total
        agreeing = sum(v >= 0.45 for v in scores.values())
        return round(min(1.0, weighted + max(0, agreeing - 1) * 0.08), 6)


class VirtualFarmMonitor:
    SENSOR_SPECS = {
        "temperature_c": (31.0, 1.2, 10.0),
        "humidity_pct": (45.0, 3.0, 25.0),
        "soil_moisture_pct": (38.0, 2.5, -25.0),
        "air_quality_index": (42.0, 4.0, 110.0),
        "light_lux_k": (35.0, 5.0, -25.0),
    }

    def __init__(self, farm_map: Path, runtime: Path, seed: int = 20260825):
        self.rng = random.Random(seed + 1000)
        self.farm = DigitalFarm(farm_map, seed)
        self.engine = RobustAnomalyEngine()
        self.chain = EvidenceChain(runtime / "environmental_evidence.jsonl")
        self.aoip = EvidenceChain(runtime / "asa_aoip_environmental_gateway.jsonl")
        self.confirm_count = 0
        self.cycles = 0
        self.privacy_yields = 0
        self.confirmed = 0
        self.false_alerts = 0
        self.hidden_incidents: set[str] = set()
        self.detected_incidents: set[str] = set()

    def _reading(self, name: str, incident: bool) -> tuple[float, float, bool]:
        base, noise, delta = self.SENSOR_SPECS[name]
        value = self.rng.gauss(base + (delta if incident else 0.0), noise)
        return round(value, 4), 1.0, True

    def cycle(self) -> dict:
        context, incident = self.farm.next_context()
        hidden = context.pop("_hidden")
        if hidden["incident_id"]:
            self.hidden_incidents.add(hidden["incident_id"])

        if context["zone_type"] == "open_privacy_safe" and hidden["human_presence"]:
            self.privacy_yields += 1
            privacy_mode = "PRIVACY_YIELD"
        else:
            privacy_mode = "PRIVATE_AUTHORIZED" if context["zone_type"] == "private_authorized" else "PRIVACY_SAFE"

        readings: dict[str, dict] = {}
        scores: dict[str, float] = {}
        health: dict[str, float] = {}
        for name in self.SENSOR_SPECS:
            value, sensor_health, valid = self._reading(name, incident)
            score = self.engine.score(name, value, sensor_health, valid)
            readings[name] = Reading(name, value, sensor_health, valid, score).__dict__
            scores[name] = score
            health[name] = sensor_health

        fused = self.engine.fuse(scores, health)
        self.confirm_count = self.confirm_count + 1 if fused >= 0.68 else 0
        active_alert = self.confirm_count >= 3

        if active_alert:
            self.confirmed += 1
            if hidden["incident_id"]:
                self.detected_incidents.add(hidden["incident_id"])
            else:
                self.false_alerts += 1
            payload = {
                "schema": "asa.aoip.environmental-evidence.v1",
                "fact": {"readings": readings, "farm_context": context},
                "inference": {"classification": "ENVIRONMENTAL_ANOMALY", "confidence": fused},
                "privacy": {
                    "mode": privacy_mode,
                    "person_tracking": False,
                    "facial_recognition": False,
                    "person_media_stored": False,
                },
                "control": {
                    "autonomous_physical_actuation": False,
                    "human_verification_required": True,
                },
            }
            event = self.chain.append("confirmed_anomaly", payload)
            self.aoip.append("environmental_evidence_ingest", {
                "source_event_hash": event["record_hash"],
                "schema": payload["schema"],
                "evidence_classification": "Internal Test Only",
                "external_connection": False,
                "production_deployment": False,
            })
            self.confirm_count = 0

        self.cycles += 1
        return {
            "cycle": self.cycles,
            "state": "PRIVACY_YIELD" if privacy_mode == "PRIVACY_YIELD" else "MONITORING",
            "zone_id": context["zone_id"],
            "fused_anomaly_score": fused,
            "active_alert": active_alert,
        }

    def run(self, cycles: int) -> dict:
        last = None
        for _ in range(cycles):
            last = self.cycle()
        chain_ok, chain_events = self.chain.verify()
        aoip_ok, aoip_events = self.aoip.verify()
        return {
            "classification": "Internal Test Only",
            "simulation_only": True,
            "real_farm_connected": False,
            "cycles": self.cycles,
            "hidden_incidents": len(self.hidden_incidents),
            "detected_incidents": len(self.detected_incidents),
            "false_alerts": self.false_alerts,
            "privacy_yields": self.privacy_yields,
            "evidence_chain": {"valid": chain_ok, "events": chain_events},
            "asa_aoip_gateway": {"valid": aoip_ok, "events": aoip_events, "external_connection": False},
            "last_state": last,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=250)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--runtime", type=Path, default=ROOT / "runtime")
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args()
    args.runtime.mkdir(parents=True, exist_ok=True)
    monitor = VirtualFarmMonitor(ROOT / "farm_map.json", args.runtime, args.seed)
    summary = monitor.run(args.cycles)
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    print(text)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(text + "\n", encoding="utf-8")
    if not summary["evidence_chain"]["valid"] or not summary["asa_aoip_gateway"]["valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
