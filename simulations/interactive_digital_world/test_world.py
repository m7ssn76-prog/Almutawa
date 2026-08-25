import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api import create_app
from interactive_bridge import build_payload
from perception import smart_perception
from world import InteractiveDigitalWorld


class PerceptionTests(unittest.TestCase):
    def test_user_examples(self):
        normal = smart_perception(
            {"T1": 61, "T2": 62, "T3": 60}, 61, 5,
            reliabilities={"T1": 0.98, "T2": 0.97, "T3": 0.95},
        )
        self.assertEqual(normal["state"], "NORMAL")
        self.assertEqual(normal["risk"], 0)

        conflict = smart_perception(
            {"T1": 95, "T2": 61, "T3": 62}, 61, 5,
            reliabilities={"T1": 0.45, "T2": 0.98, "T3": 0.97},
        )
        self.assertEqual(conflict["state"], "EVIDENCE_CONFLICT")
        self.assertIn("VERIFY_SENSOR", conflict["decision"])

        dangerous = smart_perception(
            {"T1": 95, "T2": 94, "T3": 93}, 61, 5,
            reliabilities={"T1": 0.98, "T2": 0.97, "T3": 0.96},
            severities={"T1": 5, "T2": 5, "T3": 5},
        )
        self.assertEqual(dangerous["state"], "CONFIRMED_ANOMALY")
        self.assertEqual(dangerous["risk"], 100)

    def test_invalid_data_is_insufficient(self):
        result = smart_perception({"T1": float("nan")}, 10, 2)
        self.assertEqual(result["state"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result["decision"], "REQUEST_MORE_DATA")


class WorldTests(unittest.TestCase):
    def test_commands_change_persistent_world(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            world = InteractiveDigitalWorld(runtime, seed=1)
            start = world.snapshot()
            world.apply_command("LIGHT_ON")
            after_light = world.tick(1)
            self.assertTrue(after_light["rover"]["light_on"])
            self.assertGreater(after_light["world"]["ambient_light"], start["world"]["ambient_light"])

            x0, y0 = after_light["rover"]["x"], after_light["rover"]["y"]
            world.apply_command("MOVE_FORWARD")
            moved = world.snapshot()
            self.assertNotEqual((moved["rover"]["x"], moved["rover"]["y"]), (x0, y0))

            reloaded = InteractiveDigitalWorld(runtime, seed=999)
            self.assertEqual(reloaded["rover"] if False else reloaded.snapshot()["rover"], moved["rover"])

    def test_irrigation_and_virtual_pathogen_are_causal(self):
        with tempfile.TemporaryDirectory() as td:
            world = InteractiveDigitalWorld(Path(td), seed=2)
            world.state["world"]["soil_moisture"] = 67.5
            world.state["world"]["air_temperature"] = 32.0
            initial_risk = world.state["world"]["virtual_pathogen_risk"]
            world.apply_command("IRRIGATION_ON")
            snapshot = world.tick(20)
            self.assertGreater(snapshot["world"]["soil_moisture"], 67.5)
            self.assertGreater(snapshot["world"]["virtual_pathogen_risk"], initial_risk)

    def test_sensors_off_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            world = InteractiveDigitalWorld(Path(td), seed=3)
            world.apply_command("SENSORS_OFF")
            snapshot = world.tick(1)
            self.assertEqual(snapshot["last_perception"]["state"], "INSUFFICIENT_EVIDENCE")
            self.assertEqual(snapshot["last_perception"]["decision"], "REQUEST_MORE_DATA")

    def test_geofence_rejects_exit(self):
        with tempfile.TemporaryDirectory() as td:
            world = InteractiveDigitalWorld(Path(td), seed=4)
            world.state["rover"].update({"x": 0, "y": 0, "heading": 0})
            world._save()
            snapshot = world.apply_command("MOVE_FORWARD")
            self.assertEqual((snapshot["rover"]["x"], snapshot["rover"]["y"]), (0, 0))
            self.assertFalse(snapshot["last_command"]["accepted"])

    def test_evidence_chain_detects_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            world = InteractiveDigitalWorld(Path(td), seed=5)
            world.apply_command("LIGHT_ON")
            world.tick(10)
            valid, count = world.events.verify()
            self.assertTrue(valid)
            self.assertGreater(count, 0)
            rows = world.events.path.read_text(encoding="utf-8").splitlines()
            item = json.loads(rows[-1])
            item["payload"]["tampered"] = True
            rows[-1] = json.dumps(item)
            world.events.path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            self.assertFalse(world.events.verify()[0])

    def test_bridge_rejects_non_simulation_claims(self):
        with tempfile.TemporaryDirectory() as td:
            world = InteractiveDigitalWorld(Path(td), seed=6)
            snapshot = world.tick(5)
            payload = build_payload(snapshot)
            self.assertEqual(payload["data_origin"], "synthetic")
            self.assertEqual(payload["status"], "draft")
            bad = dict(snapshot)
            bad["real_environment_connected"] = True
            with self.assertRaises(ValueError):
                build_payload(bad)

    def test_local_api_remote_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            client = TestClient(create_app(Path(td)))
            self.assertEqual(client.get("/health").status_code, 200)
            state = client.get("/api/state").json()
            self.assertFalse(state["rover"]["light_on"])
            response = client.post("/api/command", json={"command": "LIGHT_ON"})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["rover"]["light_on"])
            ticked = client.post("/api/tick", json={"seconds": 10})
            self.assertEqual(ticked.status_code, 200)
            self.assertTrue(ticked.json()["evidence_chain"]["valid"])
            self.assertEqual(client.post("/api/command", json={"command": "REAL_ACTUATOR_ON"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
