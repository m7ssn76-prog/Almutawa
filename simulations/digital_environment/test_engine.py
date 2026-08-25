import json
import tempfile
import unittest
from pathlib import Path

from engine import DigitalEnvironmentMonitor, load_profiles, run_suite, ROOT
from asa_bridge import build_knowledge_payload


class DigitalEnvironmentTests(unittest.TestCase):
    def test_profiles_are_public_safe_and_generic(self):
        profiles = load_profiles()
        self.assertGreaterEqual(len(profiles), 5)
        kinds = {p["environment_type"] for p in profiles}
        self.assertTrue({"agriculture", "warehouse", "urban_green", "industrial", "software_system"}.issubset(kinds))
        for profile in profiles:
            self.assertIsNone(profile["real_world_location"])
            self.assertFalse(profile["physical_actuation"])
            self.assertFalse(profile["person_tracking"])
            self.assertFalse(profile["facial_recognition"])
            self.assertTrue(profile["sensors"])
            self.assertTrue(profile["zones"])

    def test_each_profile_runs_with_valid_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            for index, profile in enumerate(load_profiles()):
                monitor = DigitalEnvironmentMonitor(profile, Path(td) / profile["environment_id"], 100 + index)
                summary = monitor.run(120)
                self.assertTrue(summary["simulation_only"])
                self.assertFalse(summary["real_environment_connected"])
                self.assertTrue(summary["evidence_chain"]["valid"])
                self.assertTrue(summary["asa_aoip_gateway"]["valid"])
                self.assertFalse(summary["asa_aoip_gateway"]["external_connection"])

    def test_suite_runs_all_profiles(self):
        with tempfile.TemporaryDirectory() as td:
            summary = run_suite(80, Path(td), 20260825)
            self.assertEqual(summary["environment_count"], len(load_profiles()))
            self.assertTrue(summary["all_evidence_valid"])
            self.assertFalse(summary["real_environment_connected"])
            self.assertFalse(summary["external_connection"])

    def test_bridge_is_fail_closed_and_excludes_ground_truth(self):
        with tempfile.TemporaryDirectory() as td:
            summary = run_suite(100, Path(td), 20260825)
            payload = build_knowledge_payload(summary)
            content = json.loads(payload["content"])
            self.assertEqual(content["schema"], "asa.aoip.digital-environment-suite.v1")
            self.assertEqual(payload["data_origin"], "synthetic")
            self.assertEqual(payload["status"], "draft")
            self.assertNotIn("hidden_incidents", payload["content"])
            self.assertNotIn("detected_incidents", payload["content"])
            self.assertFalse(content["boundary"]["physical_actuation"])
            self.assertFalse(content["boundary"]["person_tracking"])
            self.assertFalse(content["boundary"]["covert_monitoring"])

            bad = dict(summary)
            bad["real_environment_connected"] = True
            with self.assertRaises(ValueError):
                build_knowledge_payload(bad)


if __name__ == "__main__":
    unittest.main()
