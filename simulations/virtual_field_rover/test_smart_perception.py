import math
import unittest

from smart_perception import smart_perception


class SmartPerceptionTests(unittest.TestCase):
    def test_normal_state_has_high_state_confidence(self):
        result = smart_perception(
            {"T1": 61, "T2": 62, "T3": 60},
            baseline=61,
            tolerance=5,
            reliabilities={"T1": 0.98, "T2": 0.97, "T3": 0.95},
        )
        self.assertEqual(result["state"], "NORMAL")
        self.assertEqual(result["anomaly_support"], 0)
        self.assertGreaterEqual(result["confidence"], 95)
        self.assertEqual(result["risk"], 0)
        self.assertFalse(result["details"]["autonomous_physical_actuation"])

    def test_single_outlier_becomes_evidence_conflict(self):
        result = smart_perception(
            {"T1": 95, "T2": 61, "T3": 62},
            baseline=61,
            tolerance=5,
            reliabilities={"T1": 0.45, "T2": 0.98, "T3": 0.97},
        )
        self.assertEqual(result["state"], "EVIDENCE_CONFLICT")
        self.assertEqual(result["decision"], "VERIFY_SENSOR / OBSERVE")
        self.assertTrue(result["details"]["mixed_conflict"])

    def test_high_impact_agreement_requires_human_approval(self):
        result = smart_perception(
            {"T1": 95, "T2": 94, "T3": 93},
            baseline=61,
            tolerance=5,
            reliabilities={"T1": 0.98, "T2": 0.97, "T3": 0.96},
            severities={"T1": 5, "T2": 5, "T3": 5},
        )
        self.assertEqual(result["state"], "CONFIRMED_ANOMALY")
        self.assertEqual(result["risk"], 100)
        self.assertEqual(result["decision"], "ESCALATE / HUMAN_APPROVAL")
        self.assertTrue(result["details"]["human_approval_required_for_escalation"])

    def test_opposite_direction_anomalies_are_not_false_confirmation(self):
        result = smart_perception(
            {"T1": 95, "T2": 25, "T3": 94},
            baseline=61,
            tolerance=5,
            reliabilities={"T1": 1.0, "T2": 1.0, "T3": 1.0},
            severities={"T1": 5, "T2": 5, "T3": 5},
        )
        self.assertEqual(result["state"], "EVIDENCE_CONFLICT")
        self.assertTrue(result["details"]["directional_conflict"])
        self.assertEqual(result["anomaly_support"], 100)

    def test_one_valid_sensor_is_insufficient_evidence(self):
        result = smart_perception(
            {"T1": 61, "T2": math.nan, "T3": None},
            baseline=61,
            tolerance=5,
        )
        self.assertEqual(result["state"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result["decision"], "REQUEST_MORE_DATA")

    def test_invalid_reliability_fails_closed(self):
        result = smart_perception(
            {"T1": 61, "T2": 62},
            baseline=61,
            tolerance=5,
            reliabilities={"T1": 1.2, "T2": 1.0},
        )
        self.assertEqual(result["state"], "CONFIGURATION_ERROR")
        self.assertEqual(result["decision"], "FIX_CONFIGURATION")

    def test_invalid_tolerance_fails_closed(self):
        result = smart_perception(
            {"T1": 61, "T2": 62},
            baseline=61,
            tolerance=0,
        )
        self.assertEqual(result["state"], "CONFIGURATION_ERROR")

    def test_boolean_sensor_value_is_not_treated_as_number(self):
        result = smart_perception(
            {"T1": True, "T2": 61, "T3": 62},
            baseline=61,
            tolerance=5,
        )
        self.assertEqual(result["state"], "NORMAL")
        self.assertIn("T1", result["details"]["invalid_sensors"])


if __name__ == "__main__":
    unittest.main()
