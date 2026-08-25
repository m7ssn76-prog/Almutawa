from __future__ import annotations

from math import isfinite


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def smart_perception(sensor_values, baseline, tolerance, severities=None, reliabilities=None):
    """Fuse comparable virtual-sensor readings into an evidence-aware decision.

    This function is intentionally domain-agnostic: callers should pass readings
    that share the same scale/meaning (for example three temperature probes or
    three normalized plant-health indicators), not unrelated physical units.
    """
    if not isinstance(baseline, (int, float)) or not isfinite(baseline):
        raise ValueError("baseline must be a finite number")
    if not isinstance(tolerance, (int, float)) or not isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be a positive finite number")

    severities = severities or {k: 1 for k in sensor_values}
    reliabilities = reliabilities or {k: 1.0 for k in sensor_values}

    valid = {
        k: float(v)
        for k, v in sensor_values.items()
        if isinstance(v, (int, float)) and isfinite(v)
    }
    if not valid:
        return {
            "state": "INSUFFICIENT_EVIDENCE",
            "confidence": 0,
            "risk": 0,
            "decision": "REQUEST_MORE_DATA",
            "reason": "لا توجد بيانات حساسات صالحة",
            "details": {"values": {}, "baseline": baseline, "tolerance": tolerance},
        }

    reliability = {k: _clamp(reliabilities.get(k, 1.0), 0.0, 1.0) for k in valid}
    severity = {k: int(_clamp(severities.get(k, 1), 1, 5)) for k in valid}
    deviations = {k: abs(v - baseline) for k, v in valid.items()}
    anomalous = {k: d > tolerance for k, d in deviations.items()}

    total_weight = sum(reliability.values())
    anomaly_weight = sum(reliability[k] for k, is_anom in anomalous.items() if is_anom)
    anomaly_ratio = anomaly_weight / total_weight if total_weight else 0.0

    spread = max(valid.values()) - min(valid.values())
    anomaly_count = sum(anomalous.values())
    conflict = spread > tolerance * 2 and 0 < anomaly_count < len(valid)

    confidence = round(100 * anomaly_ratio)
    if conflict:
        confidence = max(20, round(confidence * 0.6))

    max_severity = max([severity[k] for k, is_anom in anomalous.items() if is_anom] or [1])
    risk = round((confidence / 100) * max_severity * 20)

    if conflict:
        state = "EVIDENCE_CONFLICT"
        decision = "VERIFY_SENSOR / OBSERVE"
        reason = "الحساسات لا تتفق؛ لا يُعتمد سبب واحد قبل التحقق"
    elif anomaly_ratio >= 0.67 and risk >= 60:
        state = "CONFIRMED_ANOMALY"
        decision = "ESCALATE / HUMAN_APPROVAL"
        reason = "عدة حساسات موثوقة تؤكد انحرافًا عالي الأثر"
    elif anomaly_ratio >= 0.50:
        state = "ANOMALY_SUSPECTED"
        decision = "ALERT / COLLECT_MORE_EVIDENCE"
        reason = "يوجد انحراف معتبر لكن الدليل غير كافٍ للتصرف الآلي"
    else:
        state = "NORMAL"
        decision = "OBSERVE"
        reason = "لا يوجد انحراف مؤكد يتجاوز مستوى القرار"

    return {
        "state": state,
        "confidence": confidence,
        "risk": risk,
        "decision": decision,
        "reason": reason,
        "details": {
            "values": valid,
            "baseline": baseline,
            "tolerance": tolerance,
            "deviations": deviations,
            "anomalous": anomalous,
            "spread": spread,
            "reliabilities": reliability,
            "severities": severity,
        },
    }
