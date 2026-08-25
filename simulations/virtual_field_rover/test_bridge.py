import json
import unittest

from asa_bridge import build_knowledge_payload


class BridgeTests(unittest.TestCase):
    def valid_summary(self):
        return {
            "classification": "Internal Test Only",
            "simulation_only": True,
            "real_farm_connected": False,
            "adaptive_behavior": True,
            "cycles": 100,
            "detection_rate": 0.9,
            "privacy_yields": 7,
            "privacy_reroutes": 7,
            "adaptive_revisits": 9,
            "investigation_triggers": 4,
            "degraded_sensor_cycles": 3,
            "false_alerts": 0,
            "evidence_chain": {"valid": True, "events": 2},
            "asa_aoip_gateway": {"valid": True, "events": 2, "external_connection": False},
            "last_state": {
                "state": "INVESTIGATING",
                "route_action": "REVISIT_FOR_CONFIRMATION",
                "zone_id": "PRIVATE-CORE",
            },
        }

    def test_builds_synthetic_draft_payload_with_behavior_metrics(self):
        payload = build_knowledge_payload(self.valid_summary())
        self.assertEqual(payload["data_origin"], "synthetic")
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(payload["sensitivity"], "public")
        self.assertNotIn("hidden_incidents", payload["content"])
        self.assertNotIn("detected_incidents", payload["content"])

        content = json.loads(payload["content"])
        self.assertEqual(content["schema"], "asa.aoip.digital-farm-run-summary.v2")
        self.assertTrue(content["adaptive_behavior"])
        self.assertEqual(content["privacy_reroutes"], 7)
        self.assertEqual(content["adaptive_revisits"], 9)
        self.assertEqual(content["degraded_sensor_cycles"], 3)
        self.assertEqual(content["investigation_triggers"], 4)
        self.assertEqual(content["detection_rate"], 0.9)

    def test_rejects_real_farm_state(self):
        summary = self.valid_summary()
        summary["real_farm_connected"] = True
        with self.assertRaises(ValueError):
            build_knowledge_payload(summary)

    def test_rejects_invalid_chain(self):
        summary = self.valid_summary()
        summary["evidence_chain"]["valid"] = False
        with self.assertRaises(ValueError):
            build_knowledge_payload(summary)


if __name__ == "__main__":
    unittest.main()
