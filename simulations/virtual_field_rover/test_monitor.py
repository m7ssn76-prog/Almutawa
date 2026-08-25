import json
import tempfile
import unittest
from pathlib import Path

from monitor import DigitalFarm, EvidenceChain, RobustAnomalyEngine, VirtualFarmMonitor, ROOT


class RoverTests(unittest.TestCase):
    def test_geofence_and_no_real_location(self):
        farm = DigitalFarm(ROOT / "farm_map.json", 1)
        self.assertIsNotNone(farm.zone_at(1, 1))
        self.assertIsNone(farm.zone_at(99, 99))
        self.assertIsNone(farm.cfg["real_world_location"])

    def test_evidence_chain_detects_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "e.jsonl"
            chain = EvidenceChain(path)
            chain.append("x", {"a": 1})
            self.assertEqual(chain.verify(), (True, 1))
            row = json.loads(path.read_text())
            row["payload"]["a"] = 2
            path.write_text(json.dumps(row) + "\n")
            self.assertFalse(EvidenceChain(path).verify()[0])

    def test_sensor_fusion_health_weighting(self):
        scores = {"a": 1.0, "b": 0.1}
        full = RobustAnomalyEngine.fuse(scores, {"a": 1.0, "b": 1.0})
        weak = RobustAnomalyEngine.fuse(scores, {"a": 0.0, "b": 1.0})
        self.assertGreater(full, weak)

    def test_privacy_yield_changes_next_route_to_private_zone(self):
        with tempfile.TemporaryDirectory() as td:
            monitor = VirtualFarmMonitor(ROOT / "farm_map.json", Path(td), seed=7)
            calls = []

            def fake_context(*, revisit=False, force_private=False):
                calls.append((revisit, force_private))
                if len(calls) == 1:
                    return (
                        {
                            "farm_id": "SIM",
                            "zone_id": "OPEN-EDGE",
                            "zone_type": "open_privacy_safe",
                            "position": {"x": 11, "y": 11},
                            "_hidden": {
                                "incident": False,
                                "incident_id": None,
                                "human_presence": True,
                            },
                        },
                        False,
                    )
                self.assertTrue(force_private)
                return (
                    {
                        "farm_id": "SIM",
                        "zone_id": "PRIVATE-CORE",
                        "zone_type": "private_authorized",
                        "position": {"x": 1, "y": 1},
                        "_hidden": {
                            "incident": False,
                            "incident_id": None,
                            "human_presence": False,
                        },
                    },
                    False,
                )

            monitor.farm.next_context = fake_context
            monitor._reading = lambda name, incident: (1.0, 1.0, True)
            monitor.engine.score = lambda name, value, health, valid: 0.0
            monitor.engine.fuse = lambda scores, health: 0.0

            first = monitor.cycle()
            second = monitor.cycle()

            self.assertEqual(first["state"], "PRIVACY_YIELD")
            self.assertFalse(first["active_alert"])
            self.assertEqual(second["route_action"], "REROUTE_PRIVATE")
            self.assertEqual(second["zone_id"], "PRIVATE-CORE")
            self.assertEqual(monitor.privacy_reroutes, 1)

    def test_degraded_sensor_mode_blocks_pending_alert(self):
        with tempfile.TemporaryDirectory() as td:
            monitor = VirtualFarmMonitor(ROOT / "farm_map.json", Path(td), seed=8)
            monitor.confirm_count = 2
            monitor.farm.next_context = lambda **kwargs: (
                {
                    "farm_id": "SIM",
                    "zone_id": "PRIVATE-CORE",
                    "zone_type": "private_authorized",
                    "position": {"x": 1, "y": 1},
                    "_hidden": {
                        "incident": True,
                        "incident_id": "SIM-DEGRADED",
                        "human_presence": False,
                    },
                },
                True,
            )
            healthy = {"temperature_c", "humidity_pct", "soil_moisture_pct"}
            monitor._reading = lambda name, incident: (
                (99.0, 1.0, True) if name in healthy else (0.0, 0.0, False)
            )
            monitor.engine.score = lambda name, value, health, valid: 1.0 if valid else 0.0
            monitor.engine.fuse = lambda scores, health: 1.0

            result = monitor.cycle()

            self.assertEqual(result["state"], "DEGRADED_SENSOR_MODE")
            self.assertFalse(result["active_alert"])
            self.assertEqual(result["healthy_sensors"], 3)
            self.assertEqual(monitor.confirm_count, 0)
            self.assertGreaterEqual(monitor.revisit_cycles, 1)

    def test_high_risk_signal_triggers_revisit_before_alert(self):
        with tempfile.TemporaryDirectory() as td:
            monitor = VirtualFarmMonitor(ROOT / "farm_map.json", Path(td), seed=9)
            calls = []

            def fake_context(*, revisit=False, force_private=False):
                calls.append((revisit, force_private))
                return (
                    {
                        "farm_id": "SIM",
                        "zone_id": "IRRIGATION",
                        "zone_type": "private_authorized",
                        "position": {"x": 12, "y": 2},
                        "_hidden": {
                            "incident": True,
                            "incident_id": "SIM-RISK",
                            "human_presence": False,
                        },
                    },
                    True,
                )

            monitor.farm.next_context = fake_context
            monitor._reading = lambda name, incident: (99.0, 1.0, True)
            monitor.engine.score = lambda name, value, health, valid: 1.0
            monitor.engine.fuse = lambda scores, health: 0.90

            first = monitor.cycle()
            second = monitor.cycle()
            third = monitor.cycle()

            self.assertEqual(first["state"], "INVESTIGATING")
            self.assertEqual(second["route_action"], "REVISIT_FOR_CONFIRMATION")
            self.assertTrue(calls[1][0])
            self.assertTrue(third["active_alert"])
            self.assertEqual(third["state"], "ALERT_PENDING_HUMAN_REVIEW")
            self.assertGreaterEqual(monitor.adaptive_revisits, 1)

    def test_simulation_exercises_adaptive_behavior_and_aoip_chain(self):
        with tempfile.TemporaryDirectory() as td:
            monitor = VirtualFarmMonitor(ROOT / "farm_map.json", Path(td), seed=20260825)
            summary = monitor.run(1200)
            self.assertTrue(summary["simulation_only"])
            self.assertFalse(summary["real_farm_connected"])
            self.assertTrue(summary["adaptive_behavior"])
            self.assertGreater(summary["privacy_yields"], 0)
            self.assertGreater(summary["privacy_reroutes"], 0)
            self.assertGreater(summary["adaptive_revisits"], 0)
            self.assertGreater(summary["degraded_sensor_cycles"], 0)
            self.assertTrue(summary["evidence_chain"]["valid"])
            self.assertTrue(summary["asa_aoip_gateway"]["valid"])
            self.assertFalse(summary["asa_aoip_gateway"]["external_connection"])


if __name__ == "__main__":
    unittest.main()
