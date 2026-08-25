from app.student_protection_environment import RiskLevel, StudentContext, evaluate


def test_learning_support_never_becomes_punishment():
    decision = evaluate(StudentContext(description="Student asks for help."))
    assert decision.automatic_punishment_allowed is False
    assert decision.diagnosis_allowed is False
    assert decision.retaliation_allowed is False


def test_repeated_bullying_activates_follow_up_and_confidence_support():
    decision = evaluate(
        StudentContext(
            description="Repeated bullying with power imbalance.",
            bullying_reported=True,
            repeated_pattern=True,
            power_imbalance=True,
        )
    )
    assert decision.risk_level == RiskLevel.ELEVATED
    assert decision.follow_up_required is True
    assert decision.confidence_support_required is True


def test_teacher_subject_of_complaint_requires_independent_review():
    decision = evaluate(
        StudentContext(
            description="Student reports inappropriate treatment by teacher.",
            teacher_is_subject_of_complaint=True,
        )
    )
    assert decision.admin_escalation_required is True
    assert decision.independent_review_required is True


def test_immediate_danger_outranks_confidence_training():
    decision = evaluate(
        StudentContext(
            description="Immediate safety concern.",
            immediate_danger=True,
            confidence_training_requested=True,
        )
    )
    assert decision.risk_level == RiskLevel.SAFETY
    assert decision.admin_escalation_required is True
    assert any("safe supervised setting" in action for action in decision.recommended_actions)


def test_disability_access_barrier_is_support_and_review_not_misconduct():
    decision = evaluate(
        StudentContext(
            description="Student needs an accessibility adjustment.",
            disability_or_access_need=True,
            accessibility_barrier=True,
        )
    )
    assert decision.admin_escalation_required is True
    assert any("access" in action.lower() for action in decision.recommended_actions)
    assert decision.automatic_punishment_allowed is False


def test_family_safety_concern_does_not_force_guardian_contact():
    decision = evaluate(
        StudentContext(
            description="Family may be part of the reported concern.",
            family_safety_concern=True,
        )
    )
    assert decision.guardian_contact_requires_safeguarding_judgment is True
    assert decision.independent_review_required is True
    assert any("Do not automatically contact" in check for check in decision.rights_checks)


def test_good_faith_report_is_protected_from_retaliation():
    decision = evaluate(
        StudentContext(
            description="Student reports a concern in good faith.",
            complaint_in_good_faith=True,
            privacy_risk=True,
        )
    )
    assert decision.follow_up_required is True
    assert any("retaliation" in check.lower() for check in decision.rights_checks)
    assert any("need it" in check.lower() for check in decision.rights_checks)


def test_confidence_means_safe_skills_not_fighting_back():
    decision = evaluate(
        StudentContext(
            description="Confidence practice requested.",
            confidence_training_requested=True,
            safe_adult_available=False,
        )
    )
    assert decision.confidence_support_required is True
    assert decision.admin_escalation_required is True
    assert any("never train retaliation" in action.lower() for action in decision.recommended_actions)
