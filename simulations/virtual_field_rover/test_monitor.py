import json
import tempfile
import unittest
from pathlib import Path

from monitor import (
    DigitalFarm,
    EvidenceChain,
    FlexibleEnvironmentEngine,
    RobustAnomalyEngine,
    VirtualFarmMonitor,
    ROOT,
)


class RoverTests(unittest.TestCase):
    def test_geofence_and_no_real_location(self):
        farm = DigitalFarm(ROOT / "farm_map.json", 1)
        self.assertIsNotNone(farm.zone_at(1, 1))
        self.assertIsNone(farm.zone_at(99, 99))
        self.assertIsNone(farm.cfg["real_world_location"])

    def test_flexible_environment_policy_is_fail_safe(self):
        farm = DigitalFarm(ROOT / "farm_map.json", 1)
        cfg = farm.cfg["flexible_environment"]
        self.assertEqual(cfg["layout_mode"], "modular")
        self.assertTrue(cfg["distributed_storage"])
        self.assertTrue(cfg["protected_storage"]["authorized_access_only"])
        self.assertFalse(cfg["protected_storage"]["hazardous_materials_allowed"])
        self.assertFalse(cfg["rover_dock"]["autonomous_departure"])
        self.assertFalse(
            cfg["resilience"]["physical_actuation_without_human_approval"]
        )

    def test_flexible_environment_modes(self):
        normal = FlexibleEnvironmentEngine.assess(
            network_available=True,
            battery_pct=80,
            valid_sensor_ratio=1.0,
            privacy_mode="PRIVATE_AUTHORIZED",
        )
        self.assertEqual(normal["mode"], "NORMAL")

        local = FlexibleEnvironmentEngine.assess(
            network_available=False,
            battery_pct=80,
            valid_sensor_ratio=1.0,
            privacy_mode="PRIVATE_AUTHORIZED",
        )
        self.assertEqual(local["mode"], "LOCAL_FALLBACK")

        low_power = FlexibleEnvironmentEngine.assess(
            network_available=True,
            battery_pct=15,
            valid_sensor_ratio=1.0,
            privacy_mode="PRIVATE_AUTHORIZED",
        )
        self.assertEqual(low_power["mode"], "ENERGY_SAVER")

        degraded = FlexibleEnvironmentEngine.assess(
            network_available=True,
            battery_pct=80,
            valid_sensor_ratio=0.4,
            privacy_mode="PRIVATE_AUTHORIZED",
        )
        self.assertEqual(degraded["mode"], "DEGRADED_SENSOR")

        privacy = FlexibleEnvironmentEngine.assess(
            network_available=True,
            battery_pct=80,
            valid_sensor_ratio=1.0,
            privacy_mode="PRIVACY_YIELD",
        )
        self.assertEqual(privacy["mode"], "PRIVACY_YIELD")
        self.assertFalse(privacy["external_ai_call"])
        self.assertFalse(privacy["autonomous_physical_actuation"])

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
            monitor = VirtualFarmMonitor(
                ROOT / "farm_map.json",
                Path(td),
                seed=20260825,
            )
            summary = monitor.run(400)
            self.assertTrue(summary["simulation_only"])
            self.assertFalse(summary["real_farm_connected"])
            self.assertTrue(summary["evidence_chain"]["valid"])
            self.assertTrue(summary["asa_aoip_gateway"]["valid"])
            self.assertFalse(summary["asa_aoip_gateway"]["external_connection"])
            self.assertEqual(sum(summary["flexibility_modes"].values()), 400)
            self.assertFalse(summary["openai_advisory"]["external_call_made"])
            self.assertFalse(
                summary["openai_advisory"]["autonomous_physical_actuation"]
            )
            self.assertTrue(
                summary["protected_storage"]["authorized_access_only"]
            )
            self.assertFalse(
                summary["protected_storage"]["hazardous_materials_allowed"]
            )


if __name__ == "__main__":
    unittest.main()
