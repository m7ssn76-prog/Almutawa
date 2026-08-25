import unittest
from asa_bridge import build_knowledge_payload


class BridgeTests(unittest.TestCase):
    def valid_summary(self):
        return {
            "classification": "Internal Test Only",
            "simulation_only": True,
            "real_farm_connected": False,
            "cycles": 100,
            "privacy_yields": 7,
            "false_alerts": 0,
            "evidence_chain": {"valid": True, "events": 2},
            "asa_aoip_gateway": {"valid": True, "events": 2, "external_connection": False},
            "last_state": {"state": "MONITORING", "zone_id": "PRIVATE-CORE"},
        }

    def test_builds_synthetic_draft_payload(self):
        payload = build_knowledge_payload(self.valid_summary())
        self.assertEqual(payload["data_origin"], "synthetic")
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(payload["sensitivity"], "public")
        self.assertNotIn("hidden_incidents", payload["content"])
        self.assertNotIn("detected_incidents", payload["content"])

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
