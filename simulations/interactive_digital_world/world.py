from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from pathlib import Path

from perception import smart_perception


WORLD_SIZE = 20
ALLOWED_COMMANDS = {
    "MOVE_FORWARD",
    "MOVE_BACKWARD",
    "TURN_LEFT",
    "TURN_RIGHT",
    "LIGHT_ON",
    "LIGHT_OFF",
    "SENSORS_ON",
    "SENSORS_OFF",
    "IRRIGATION_ON",
    "IRRIGATION_OFF",
    "AUTO_ON",
    "AUTO_OFF",
    "STOP",
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class HashEventLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def canonical(value: dict) -> bytes:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _previous_hash(self) -> str:
        if not self.path.exists():
            return "0" * 64
        lines = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            return "0" * 64
        return json.loads(lines[-1])["record_hash"]

    def append(self, event_type: str, payload: dict) -> dict:
        record = {
            "event_type": event_type,
            "timestamp": time.time(),
            "classification": "Internal Test Only",
            "source_type": "interactive_digital_world",
            "payload": payload,
            "previous_hash": self._previous_hash(),
        }
        record["record_hash"] = hashlib.sha256(self.canonical(record)).hexdigest()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def verify(self) -> tuple[bool, int]:
        if not self.path.exists():
            return True, 0
        previous = "0" * 64
        count = 0
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            item = json.loads(raw)
            claimed = item.pop("record_hash")
            if item.get("previous_hash") != previous:
                return False, count
            actual = hashlib.sha256(self.canonical(item)).hexdigest()
            if actual != claimed:
                return False, count
            previous = claimed
            count += 1
        return True, count


class InteractiveDigitalWorld:
    """Persistent, interactive, simulation-only world with causal state changes."""

    def __init__(self, runtime: Path, seed: int = 20260825):
        self.runtime = runtime
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.state_path = runtime / "world_state.json"
        self.events = HashEventLog(runtime / "world_events.jsonl")
        self.rng = random.Random(seed)
        self.state = self._load_or_create_state()

    def _load_or_create_state(self) -> dict:
        if self.state_path.exists():
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if state.get("simulation_only") is not True or state.get("real_environment_connected") is not False:
                raise ValueError("Interactive world must remain simulation-only")
            return state
        state = {
            "schema": "asa.aoip.interactive-digital-world.v1",
            "classification": "Internal Test Only",
            "simulation_only": True,
            "real_environment_connected": False,
            "physical_actuation": False,
            "clock_seconds": 0,
            "sequence": 0,
            "world": {
                "size": WORLD_SIZE,
                "air_temperature": 32.0,
                "ambient_light": 35.0,
                "soil_moisture": 48.0,
                "plant_health": 92.0,
                "virtual_pathogen_risk": 8.0,
                "irrigation_on": False,
            },
            "rover": {
                "x": 10,
                "y": 10,
                "heading": 0,
                "mode": "MANUAL",
                "moving": False,
                "light_on": False,
                "sensors_on": True,
                "battery": 100.0,
            },
            "last_command": None,
            "last_perception": None,
        }
        self._save()
        self.events.append("WORLD_CREATED", self._public_state())
        return state

    def _save(self) -> None:
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _public_state(self) -> dict:
        return json.loads(json.dumps(self.state, ensure_ascii=False))

    def _move(self, direction: int) -> bool:
        rover = self.state["rover"]
        radians = math.radians(rover["heading"])
        dx = round(math.sin(radians)) * direction
        dy = -round(math.cos(radians)) * direction
        nx, ny = rover["x"] + dx, rover["y"] + dy
        if not (0 <= nx < WORLD_SIZE and 0 <= ny < WORLD_SIZE):
            self.events.append("COMMAND_REJECTED_GEOFENCE", {"x": nx, "y": ny})
            rover["moving"] = False
            return False
        rover["x"], rover["y"] = nx, ny
        rover["moving"] = True
        rover["battery"] = _clamp(rover["battery"] - 0.18, 0.0, 100.0)
        return True

    def apply_command(self, command: str) -> dict:
        command = command.strip().upper()
        if command not in ALLOWED_COMMANDS:
            raise ValueError(f"Unsupported virtual command: {command}")
        rover = self.state["rover"]
        world = self.state["world"]
        before = self.snapshot(include_integrity=False)
        accepted = True

        if rover["battery"] <= 2 and command not in {"STOP", "SENSORS_OFF", "LIGHT_OFF", "IRRIGATION_OFF"}:
            accepted = False
        elif command == "MOVE_FORWARD":
            accepted = self._move(1)
        elif command == "MOVE_BACKWARD":
            accepted = self._move(-1)
        elif command == "TURN_LEFT":
            rover["heading"] = (rover["heading"] - 90) % 360
            rover["moving"] = False
        elif command == "TURN_RIGHT":
            rover["heading"] = (rover["heading"] + 90) % 360
            rover["moving"] = False
        elif command == "LIGHT_ON":
            rover["light_on"] = True
        elif command == "LIGHT_OFF":
            rover["light_on"] = False
        elif command == "SENSORS_ON":
            rover["sensors_on"] = True
        elif command == "SENSORS_OFF":
            rover["sensors_on"] = False
        elif command == "IRRIGATION_ON":
            world["irrigation_on"] = True
        elif command == "IRRIGATION_OFF":
            world["irrigation_on"] = False
        elif command == "AUTO_ON":
            rover["mode"] = "AUTO_PATROL"
        elif command == "AUTO_OFF":
            rover["mode"] = "MANUAL"
            rover["moving"] = False
        elif command == "STOP":
            rover["moving"] = False
            rover["mode"] = "MANUAL"

        self.state["sequence"] += 1
        self.state["last_command"] = {"command": command, "accepted": accepted}
        self._save()
        self.events.append(
            "USER_VIRTUAL_COMMAND",
            {
                "command": command,
                "accepted": accepted,
                "before_hash": hashlib.sha256(HashEventLog.canonical(before)).hexdigest(),
                "after": {"rover": self.state["rover"], "world": self.state["world"]},
            },
        )
        return self.snapshot()

    def _auto_patrol_step(self) -> None:
        rover = self.state["rover"]
        if rover["mode"] != "AUTO_PATROL" or rover["battery"] <= 5:
            return
        if not self._move(1):
            rover["heading"] = (rover["heading"] + 90) % 360

    def _evolve_one_second(self) -> None:
        world = self.state["world"]
        rover = self.state["rover"]
        self.state["clock_seconds"] += 1
        t = self.state["clock_seconds"]

        world["air_temperature"] = round(32 + 4 * math.sin(t / 180), 3)
        natural_light = 35 + 15 * math.sin(t / 120)
        world["ambient_light"] = round(_clamp(natural_light + (45 if rover["light_on"] else 0), 0, 100), 3)

        moisture_delta = 0.65 if world["irrigation_on"] else -0.08
        world["soil_moisture"] = round(_clamp(world["soil_moisture"] + moisture_delta, 5, 95), 3)

        warm_wet = world["air_temperature"] >= 31 and world["soil_moisture"] >= 68
        pathogen_delta = 0.55 if warm_wet else -0.18
        world["virtual_pathogen_risk"] = round(
            _clamp(world["virtual_pathogen_risk"] + pathogen_delta, 0, 100), 3
        )

        healthy_moisture = 30 <= world["soil_moisture"] <= 65
        health_delta = 0.05 if healthy_moisture and world["virtual_pathogen_risk"] < 35 else -0.12
        world["plant_health"] = round(_clamp(world["plant_health"] + health_delta, 0, 100), 3)

        drain = 0.006
        if rover["light_on"]:
            drain += 0.012
        if rover["sensors_on"]:
            drain += 0.008
        rover["battery"] = round(_clamp(rover["battery"] - drain, 0, 100), 3)
        if rover["battery"] <= 2:
            rover["moving"] = False
            rover["mode"] = "MANUAL"
            rover["light_on"] = False

        self._auto_patrol_step()

    def sense(self) -> dict:
        rover = self.state["rover"]
        world = self.state["world"]
        if not rover["sensors_on"]:
            result = smart_perception({}, baseline=15, tolerance=20)
            self.state["last_perception"] = result
            return result

        signal = _clamp(
            8
            + world["virtual_pathogen_risk"] * 0.86
            + max(0, 75 - world["plant_health"]) * 0.45,
            0,
            100,
        )
        values = {
            "P1": round(signal + self.rng.gauss(0, 1.5), 3),
            "P2": round(signal + self.rng.gauss(0, 1.8), 3),
            "P3": round(signal + self.rng.gauss(0, 2.0), 3),
        }
        result = smart_perception(
            values,
            baseline=15,
            tolerance=20,
            reliabilities={"P1": 0.98, "P2": 0.95, "P3": 0.92},
            severities={"P1": 5, "P2": 5, "P3": 5},
        )
        self.state["last_perception"] = result
        return result

    def tick(self, seconds: int = 1) -> dict:
        if not isinstance(seconds, int) or not 1 <= seconds <= 600:
            raise ValueError("seconds must be an integer between 1 and 600")
        for _ in range(seconds):
            self._evolve_one_second()
        perception = self.sense()
        self.state["sequence"] += 1
        self._save()
        if perception["state"] != "NORMAL" or seconds >= 10:
            self.events.append(
                "WORLD_OBSERVATION",
                {
                    "clock_seconds": self.state["clock_seconds"],
                    "position": {"x": self.state["rover"]["x"], "y": self.state["rover"]["y"]},
                    "perception": {
                        "state": perception["state"],
                        "confidence": perception["confidence"],
                        "risk": perception["risk"],
                        "decision": perception["decision"],
                    },
                    "virtual_pathogen_risk": self.state["world"]["virtual_pathogen_risk"],
                    "plant_health": self.state["world"]["plant_health"],
                },
            )
        return self.snapshot()

    def snapshot(self, include_integrity: bool = True) -> dict:
        snap = self._public_state()
        if include_integrity:
            valid, count = self.events.verify()
            snap["evidence_chain"] = {"valid": valid, "events": count}
        return snap


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, default=Path(__file__).resolve().parent / "runtime")
    parser.add_argument("--ticks", type=int, default=90)
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args()

    world = InteractiveDigitalWorld(args.runtime)
    for command in ("LIGHT_ON", "MOVE_FORWARD", "TURN_RIGHT", "MOVE_FORWARD", "IRRIGATION_ON"):
        world.apply_command(command)
    snapshot = world.tick(args.ticks)
    text = json.dumps(snapshot, ensure_ascii=False, indent=2)
    print(text)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(text + "\n", encoding="utf-8")
    if not snapshot["evidence_chain"]["valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
