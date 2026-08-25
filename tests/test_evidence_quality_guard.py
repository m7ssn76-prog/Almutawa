from app.evidence_quality_guard import apply_degraded_evidence_guard


def _result(state="NORMAL", decision="OBSERVE", accepted=None, rejected=None):
    return {
        "state": state,
        "decision": decision,
        "risk": 1.0,
        "reason": "base",
        "details": {
            "accepted": accepted or {},
            "rejected": rejected or {},
        },
    }


def test_good_evidence_keeps_normal_state():
    result = _result(accepted={"temperature": 22, "pressure": 1.0})
    guarded = apply_degraded_evidence_guard(result)

    assert guarded["state"] == "NORMAL"
    assert guarded["evidence_quality"] == "GOOD"
    assert guarded["degraded_evidence"] is False
    assert guarded["evidence_metrics"]["coverage_ratio"] == 1.0


def test_partial_rejection_degrades_normal_state():
    result = _result(
        accepted={"temperature": 22, "pressure": 1.0, "humidity": 40},
        rejected={"boolean_flag": "not-a-bool"},
    )
    guarded = apply_degraded_evidence_guard(result)

    assert guarded["state"] == "DEGRADED_NORMAL"
    assert guarded["decision"] == "VERIFY_INPUTS / OBSERVE"
    assert guarded["evidence_quality"] == "DEGRADED"
    assert guarded["evidence_metrics"]["coverage_ratio"] == 0.75
    assert guarded["evidence_metrics"]["rejected_ratio"] == 0.25


def test_half_rejected_becomes_insufficient_for_normal_state():
    result = _result(
        accepted={"temperature": 22},
        rejected={"reliability": -1},
    )
    guarded = apply_degraded_evidence_guard(result)

    assert guarded["state"] == "INSUFFICIENT_EVIDENCE"
    assert guarded["decision"] == "VERIFY_INPUTS"
    assert guarded["evidence_quality"] == "INSUFFICIENT"
    assert guarded["evidence_metrics"]["rejected_ratio"] == 0.5


def test_existing_alert_is_never_downgraded_by_rejected_input():
    result = _result(
        state="ALERT",
        decision="STOP / INSPECT",
        accepted={"temperature": 90, "pressure": 5.0},
        rejected={"boolean_flag": "bad"},
    )
    guarded = apply_degraded_evidence_guard(result)

    assert guarded["state"] == "ALERT"
    assert guarded["decision"] == "STOP / INSPECT"
    assert guarded["evidence_quality"] == "DEGRADED"
    assert "evidence_quality_warning" in guarded


def test_all_rejected_preserves_existing_alert():
    result = _result(
        state="ALERT",
        decision="STOP / INSPECT",
        accepted={},
        rejected={"temperature": "bad", "pressure": None},
    )
    guarded = apply_degraded_evidence_guard(result)

    assert guarded["state"] == "ALERT"
    assert guarded["decision"] == "STOP / INSPECT"
    assert guarded["evidence_quality"] == "INSUFFICIENT"
    assert guarded["evidence_metrics"]["coverage_ratio"] == 0.0


def test_rejected_critical_field_escalates_normal_state():
    result = _result(
        accepted={"temperature": 22, "pressure": 1.0},
        rejected={"severity": 99},
    )
    guarded = apply_degraded_evidence_guard(result)

    assert guarded["state"] == "CRITICAL_DEGRADED"
    assert guarded["decision"] == "VERIFY_CRITICAL_INPUTS / OBSERVE"
    assert guarded["evidence_quality"] == "CRITICAL_DEGRADED"
    assert guarded["evidence_metrics"]["critical_rejected_fields"] == ["severity"]


def test_no_inputs_becomes_insufficient_evidence():
    result = _result(accepted={}, rejected={})
    guarded = apply_degraded_evidence_guard(result)

    assert guarded["state"] == "INSUFFICIENT_EVIDENCE"
    assert guarded["decision"] == "VERIFY_INPUTS"
    assert guarded["evidence_quality"] == "INSUFFICIENT"
    assert guarded["evidence_metrics"]["total_count"] == 0


def test_invalid_threshold_is_rejected():
    result = _result(accepted={"temperature": 22})

    try:
        apply_degraded_evidence_guard(result, insufficient_ratio=1.5)
    except ValueError as exc:
        assert "between 0 and 1" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid insufficient_ratio")
