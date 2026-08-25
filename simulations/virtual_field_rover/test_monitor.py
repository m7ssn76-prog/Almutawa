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

    def test_simulation_privacy_and_aoip_chain(self):
        with tempfile.TemporaryDirectory() as td:
            monitor = VirtualFarmMonitor(ROOT / "farm_map.json", Path(td), seed=20260825)
            summary = monitor.run(400)
            self.assertTrue(summary["simulation_only"])
            self.assertFalse(summary["real_farm_connected"])
            self.assertTrue(summary["evidence_chain"]["valid"])
            self.assertTrue(summary["asa_aoip_gateway"]["valid"])
            self.assertFalse(summary["asa_aoip_gateway"]["external_connection"])


if __name__ == "__main__":
    unittest.main()
