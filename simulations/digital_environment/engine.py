from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent


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
            "source_type": "synthetic_digital_environment",
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
            if item.get("previous_hash") != previous:
                return False, count
            actual = hashlib.sha256(self.canonical(item)).hexdigest()
            if actual != claimed:
                return False, count
            previous = claimed
            count += 1
        return True, count


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
        mad = max(statistics.median(deviations), 0.01)
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


class EnvironmentProfile:
    def __init__(self, raw: dict, seed: int):
        self.raw = raw
        self.rng = random.Random(seed)
        self.index = 0
        self.last_point: dict | None = None
        self.incident_remaining = 0
        self.incident_id: str | None = None
        self._validate()

    def _validate(self) -> None:
        if self.raw.get("real_world_location") is not None:
            raise ValueError("Public synthetic profile must not contain a real-world location")
        if self.raw.get("physical_actuation") is not False:
            raise ValueError("Physical actuation must remain disabled")
        if self.raw.get("person_tracking") is not False:
            raise ValueError("Person tracking must remain disabled")
        if self.raw.get("facial_recognition") is not False:
            raise ValueError("Facial recognition must remain disabled")
        if not self.raw.get("sensors") or not self.raw.get("zones") or not self.raw.get("waypoints"):
            raise ValueError("Profile is missing sensors, zones, or waypoints")

    @property
    def environment_id(self) -> str:
        return self.raw["environment_id"]

    @property
    def environment_type(self) -> str:
        return self.raw["environment_type"]

    def zone_at(self, x: int, y: int) -> dict | None:
        for zone in self.raw["zones"]:
            if zone["x1"] <= x <= zone["x2"] and zone["y1"] <= y <= zone["y2"]:
                return zone
        return None

    def _next_waypoint(self, force_private: bool = False) -> dict:
        for _ in range(len(self.raw["waypoints"])):
            point = self.raw["waypoints"][self.index % len(self.raw["waypoints"])]
            self.index += 1
            zone = self.zone_at(point["x"], point["y"])
            if zone is None:
                raise RuntimeError("Waypoint outside declared environment geofence")
            if not force_private or zone["type"] == "private_authorized":
                return point
        raise RuntimeError("No private-authorized waypoint is available")

    def next_context(self, *, revisit: bool = False, force_private: bool = False) -> tuple[dict, dict]:
        if revisit and self.last_point is not None:
            point = self.last_point
        else:
            point = self._next_waypoint(force_private=force_private)
            self.last_point = point
        zone = self.zone_at(point["x"], point["y"])
        if zone is None:
            raise RuntimeError("Waypoint outside geofence")

        if self.incident_remaining <= 0 and self.rng.random() < float(self.raw["incident_probability"]):
            self.incident_remaining = self.rng.randint(4, 8)
            self.incident_id = f"SIM-{uuid.uuid4().hex[:10]}"
        incident = self.incident_remaining > 0
        if incident:
            self.incident_remaining -= 1
        else:
            self.incident_id = None

        privacy_zone = zone["type"] == "open_privacy_safe"
        human_presence = bool(self.raw["privacy_yield_enabled"] and privacy_zone and self.rng.random() < 0.20)
        public_context = {
            "environment_id": self.environment_id,
            "environment_type": self.environment_type,
            "zone_id": zone["id"],
            "zone_type": zone["type"],
            "logical_position": point,
        }
        hidden = {
            "incident": incident,
            "incident_id": self.incident_id,
            "human_presence": human_presence,
        }
        return public_context, hidden


class DigitalEnvironmentMonitor:
    SENSOR_FAULT_PROBABILITY = 0.03
    INVESTIGATION_THRESHOLD = 0.45
    ALERT_THRESHOLD = 0.68
    CONFIRMATIONS_REQUIRED = 3
    INVESTIGATION_REVISITS = 2

    def __init__(self, profile: dict, runtime: Path, seed: int):
        self.profile = EnvironmentProfile(profile, seed)
        self.rng = random.Random(seed + 1000)
        self.engine = RobustAnomalyEngine()
        self.chain = EvidenceChain(runtime / "environmental_evidence.jsonl")
        self.aoip = EvidenceChain(runtime / "asa_aoip_environmental_gateway.jsonl")
        self.confirm_count = 0
        self.revisit_cycles = 0
        self.force_private_next = False
        self.cycles = 0
        self.privacy_yields = 0
        self.privacy_reroutes = 0
        self.adaptive_revisits = 0
        self.degraded_sensor_cycles = 0
        self.hidden_incidents: set[str] = set()
        self.detected_incidents: set[str] = set()
        self.false_alerts = 0

    def _reading(self, sensor: str, spec: dict, incident: bool) -> tuple[float, float, bool]:
        value = self.rng.gauss(float(spec["base"]) + (float(spec["incident_delta"]) if incident else 0.0), float(spec["noise"]))
        if self.rng.random() < self.SENSOR_FAULT_PROBABILITY:
            return round(value, 6), 0.0, False
        return round(value, 6), 1.0, True

    def cycle(self) -> dict:
        revisit = self.revisit_cycles > 0
        context, hidden = self.profile.next_context(revisit=revisit, force_private=self.force_private_next)
        if revisit:
            self.revisit_cycles -= 1
            self.adaptive_revisits += 1
        if self.force_private_next:
            self.force_private_next = False
            self.privacy_reroutes += 1

        if hidden["incident_id"]:
            self.hidden_incidents.add(hidden["incident_id"])

        privacy_yield = hidden["human_presence"] is True
        if privacy_yield:
            self.privacy_yields += 1
            self.confirm_count = 0
            self.revisit_cycles = 0
            self.force_private_next = True
            state = "PRIVACY_YIELD"
        else:
            state = "MONITORING"

        readings: dict[str, dict] = {}
        scores: dict[str, float] = {}
        health: dict[str, float] = {}
        healthy = 0
        for name, spec in self.profile.raw["sensors"].items():
            value, sensor_health, valid = self._reading(name, spec, hidden["incident"])
            score = self.engine.score(name, value, sensor_health, valid)
            readings[name] = {"value": value, "health": sensor_health, "valid": valid, "anomaly_score": score}
            scores[name] = score
            health[name] = sensor_health
            if valid and sensor_health >= 0.5:
                healthy += 1

        minimum_healthy = max(2, len(readings) - 1)
        fused = self.engine.fuse(scores, health)
        active_alert = False
        if not privacy_yield:
            if healthy < minimum_healthy:
                self.degraded_sensor_cycles += 1
                self.confirm_count = 0
                self.revisit_cycles = max(self.revisit_cycles, 1)
                state = "DEGRADED_SENSOR_MODE"
            elif fused >= self.ALERT_THRESHOLD:
                self.confirm_count += 1
                if self.confirm_count < self.CONFIRMATIONS_REQUIRED:
                    self.revisit_cycles = max(self.revisit_cycles, self.INVESTIGATION_REVISITS)
                    state = "INVESTIGATING"
                else:
                    active_alert = True
                    state = "ALERT_PENDING_HUMAN_REVIEW"
            elif fused >= self.INVESTIGATION_THRESHOLD:
                self.confirm_count = 0
                self.revisit_cycles = max(self.revisit_cycles, self.INVESTIGATION_REVISITS)
                state = "INVESTIGATING"
            else:
                self.confirm_count = 0

        if active_alert:
            if hidden["incident_id"]:
                self.detected_incidents.add(hidden["incident_id"])
            else:
                self.false_alerts += 1
            payload = {
                "schema": "asa.aoip.environmental-evidence.v3",
                "fact": {"readings": readings, "environment_context": context},
                "inference": {"classification": "ENVIRONMENTAL_ANOMALY", "confidence": fused},
                "privacy": {
                    "mode": "PRIVACY_YIELD" if privacy_yield else "POLICY_SAFE",
                    "person_tracking": False,
                    "facial_recognition": False,
                    "person_media_stored": False,
                },
                "control": {
                    "behavior_state": state,
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
            self.revisit_cycles = 0

        self.cycles += 1
        return {
            "cycle": self.cycles,
            "state": state,
            "environment_id": self.profile.environment_id,
            "environment_type": self.profile.environment_type,
            "zone_id": context["zone_id"],
            "healthy_sensors": healthy,
            "fused_anomaly_score": fused,
            "active_alert": active_alert,
        }

    def run(self, cycles: int) -> dict:
        last = None
        for _ in range(cycles):
            last = self.cycle()
        evidence_ok, evidence_events = self.chain.verify()
        aoip_ok, aoip_events = self.aoip.verify()
        hidden_count = len(self.hidden_incidents)
        detected_count = len(self.detected_incidents)
        return {
            "classification": "Internal Test Only",
            "simulation_only": True,
            "real_environment_connected": False,
            "environment_id": self.profile.environment_id,
            "environment_type": self.profile.environment_type,
            "cycles": self.cycles,
            "hidden_incidents": hidden_count,
            "detected_incidents": detected_count,
            "detection_rate": round(detected_count / hidden_count, 6) if hidden_count else 0.0,
            "false_alerts": self.false_alerts,
            "privacy_yields": self.privacy_yields,
            "privacy_reroutes": self.privacy_reroutes,
            "adaptive_revisits": self.adaptive_revisits,
            "degraded_sensor_cycles": self.degraded_sensor_cycles,
            "evidence_chain": {"valid": evidence_ok, "events": evidence_events},
            "asa_aoip_gateway": {"valid": aoip_ok, "events": aoip_events, "external_connection": False},
            "last_state": last,
        }


def load_profiles(path: Path = ROOT / "profiles.json") -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    profiles = raw.get("profiles", [])
    ids = [p.get("environment_id") for p in profiles]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate environment_id")
    return profiles


def run_suite(cycles: int, runtime: Path, seed: int) -> dict:
    results = []
    for index, profile in enumerate(load_profiles()):
        monitor = DigitalEnvironmentMonitor(profile, runtime / profile["environment_id"], seed + index * 100)
        results.append(monitor.run(cycles))
    return {
        "classification": "Internal Test Only",
        "simulation_only": True,
        "real_environment_connected": False,
        "environment_count": len(results),
        "environment_types": [r["environment_type"] for r in results],
        "all_evidence_valid": all(r["evidence_chain"]["valid"] and r["asa_aoip_gateway"]["valid"] for r in results),
        "external_connection": False,
        "profiles": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--runtime", type=Path, default=ROOT / "runtime")
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args()
    summary = run_suite(args.cycles, args.runtime, args.seed)
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    print(text)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(text + "\n", encoding="utf-8")
    if not summary["all_evidence_valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
