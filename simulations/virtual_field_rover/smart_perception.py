from __future__ import annotations

from math import isfinite
from typing import Mapping


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
    )


def apply_degraded_evidence_guard(result: dict) -> dict:
    """Downgrade apparently normal results when some inputs were rejected.

    Existing risk/anomaly states are preserved. The guard only makes evidence
    quality explicit and never authorizes physical actuation.
    """
    details = result.get("details", {})
    rejected = details.get("rejected", {}) if isinstance(details, dict) else {}

    if rejected:
        if result.get("state") == "NORMAL":
            result["state"] = "DEGRADED_NORMAL"
            result["decision"] = "VERIFY_INPUTS / OBSERVE"
            result["reason"] = (
                "القراءات المقبولة تبدو طبيعية، لكن بعض المدخلات رُفضت؛ "
                "لا تُعامل الحالة كطبيعية كاملة قبل التحقق من جودة البيانات."
            )
        else:
            result["evidence_quality_warning"] = (
                "بعض المدخلات رُفضت؛ القرار الحالي قائم على الحساسات الصالحة فقط."
            )
    return result


def _terminal(
    *,
    state: str,
    decision: str,
    reason: str,
    details: dict | None = None,
) -> dict:
    result = {
        "state": state,
        "confidence": 0,
        "anomaly_support": 0,
        "evidence_quality": 0,
        "risk": 0,
        "decision": decision,
        "reason": reason,
    }
    if details is not None:
        result["details"] = details
    return apply_degraded_evidence_guard(result)


def smart_perception(
    sensor_values: Mapping[str, object],
    baseline: float,
    tolerance: float,
    severities: Mapping[str, object] | None = None,
    reliabilities: Mapping[str, object] | None = None,
) -> dict:
    """Assess redundant sensors measuring the same physical quantity.

    Invalid per-sensor inputs are rejected individually. A decision is made only
    from the remaining valid sensors when at least two independently weighted
    readings remain. This is decision support only and never performs physical
    actuation. Sensors with different units or meanings must not be mixed in one
    call.
    """

    if not _is_finite_number(baseline):
        return _terminal(
            state="CONFIGURATION_ERROR",
            decision="FIX_CONFIGURATION",
            reason="baseline غير صالح",
        )
    if not _is_finite_number(tolerance) or float(tolerance) <= 0:
        return _terminal(
            state="CONFIGURATION_ERROR",
            decision="FIX_CONFIGURATION",
            reason="tolerance يجب أن تكون قيمة موجبة وصالحة",
        )

    severities = severities or {}
    reliabilities = reliabilities or {}

    valid: dict[str, float] = {}
    clean_reliabilities: dict[str, float] = {}
    clean_severities: dict[str, float] = {}
    rejected: dict[str, dict[str, str]] = {}

    for key, value in sensor_values.items():
        if not _is_finite_number(value):
            rejected[key] = {
                "field": "value",
                "reason": "INVALID_SENSOR_VALUE",
            }
            continue

        reliability = reliabilities.get(key, 1.0)
        if not _is_finite_number(reliability) or not 0 <= float(reliability) <= 1:
            rejected[key] = {
                "field": "reliability",
                "reason": "OUT_OF_RANGE_0_1",
            }
            continue

        severity = severities.get(key, 1)
        if not _is_finite_number(severity) or not 1 <= float(severity) <= 5:
            rejected[key] = {
                "field": "severity",
                "reason": "OUT_OF_RANGE_1_5",
            }
            continue

        valid[key] = float(value)
        clean_reliabilities[key] = float(reliability)
        clean_severities[key] = float(severity)

    effective = [key for key in valid if clean_reliabilities[key] > 0]
    total_weight = sum(clean_reliabilities[key] for key in effective)
    if len(effective) < 2 or total_weight <= 0:
        return _terminal(
            state="INSUFFICIENT_EVIDENCE",
            decision="REQUEST_MORE_DATA",
            reason="لا يوجد وزن موثوق كافٍ من حساسين مستقلين",
            details={
                "values": valid,
                "reliabilities": clean_reliabilities,
                "severities": clean_severities,
                "rejected": rejected,
                "autonomous_physical_actuation": False,
            },
        )

    baseline_value = float(baseline)
    tolerance_value = float(tolerance)
    signed_deviations = {
        key: valid[key] - baseline_value
        for key in valid
    }
    deviations = {
        key: abs(signed_deviations[key])
        for key in valid
    }
    anomalous = {
        key: deviations[key] > tolerance_value
        for key in valid
    }
    anomalous_keys = [
        key for key in effective if anomalous[key]
    ]

    anomaly_weight = sum(clean_reliabilities[key] for key in anomalous_keys)
    anomaly_ratio = anomaly_weight / total_weight
    anomaly_support = round(100 * anomaly_ratio)
    evidence_quality = round(100 * (total_weight / len(effective)))

    spread = max(valid[key] for key in effective) - min(valid[key] for key in effective)
    high_weight = sum(
        clean_reliabilities[key]
        for key in anomalous_keys
        if signed_deviations[key] > 0
    )
    low_weight = sum(
        clean_reliabilities[key]
        for key in anomalous_keys
        if signed_deviations[key] < 0
    )

    directional_conflict = (
        high_weight > 0
        and low_weight > 0
        and min(high_weight, low_weight) / total_weight >= 0.20
    )
    mixed_conflict = (
        spread > tolerance_value * 2
        and 0 < len(anomalous_keys) < len(effective)
    )
    conflict = directional_conflict or mixed_conflict

    if anomalous_keys:
        weighted_severity = sum(
            clean_reliabilities[key] * clean_severities[key]
            for key in anomalous_keys
        ) / anomaly_weight
        magnitude = min(
            1.0,
            max(deviations[key] for key in anomalous_keys) / (tolerance_value * 3),
        )
        risk = round(anomaly_ratio * weighted_severity * 20 * magnitude)
    else:
        risk = 0
    risk = max(0, min(100, risk))

    if conflict:
        state = "EVIDENCE_CONFLICT"
        decision = "VERIFY_SENSOR / OBSERVE"
        reason = "الحساسات لا تتفق؛ لا يُعتمد سبب واحد قبل التحقق"
        state_confidence = max(20, round(evidence_quality * 0.75))
    elif (
        anomaly_ratio >= 0.67
        and len(anomalous_keys) >= 2
        and evidence_quality >= 60
        and risk >= 60
    ):
        state = "CONFIRMED_ANOMALY"
        decision = "ESCALATE / HUMAN_APPROVAL"
        reason = "عدة حساسات موثوقة تؤكد انحرافًا عالي الأثر"
        state_confidence = round((anomaly_support * evidence_quality) / 100)
    elif anomaly_ratio >= 0.50 or (
        anomaly_ratio >= 0.33
        and any(clean_severities[key] >= 4 for key in anomalous_keys)
    ):
        state = "ANOMALY_SUSPECTED"
        decision = "ALERT / COLLECT_MORE_EVIDENCE"
        reason = "يوجد انحراف معتبر لكن الدليل غير كافٍ للتصرف الآلي"
        state_confidence = round((anomaly_support * evidence_quality) / 100)
    else:
        state = "NORMAL"
        decision = "OBSERVE"
        reason = "لا يوجد انحراف مؤكد يتجاوز مستوى القرار"
        state_confidence = round(
            ((100 - anomaly_support) * evidence_quality) / 100
        )

    result = {
        "state": state,
        "confidence": state_confidence,
        "anomaly_support": anomaly_support,
        "evidence_quality": evidence_quality,
        "risk": risk,
        "decision": decision,
        "reason": reason,
        "details": {
            "values": valid,
            "baseline": baseline_value,
            "tolerance": tolerance_value,
            "signed_deviations": signed_deviations,
            "deviations": deviations,
            "anomalous": anomalous,
            "reliabilities": clean_reliabilities,
            "severities": clean_severities,
            "rejected": rejected,
            "spread": spread,
            "directional_conflict": directional_conflict,
            "mixed_conflict": mixed_conflict,
            "same_quantity_required": True,
            "human_approval_required_for_escalation": True,
            "autonomous_physical_actuation": False,
        },
    }
    return apply_degraded_evidence_guard(result)
