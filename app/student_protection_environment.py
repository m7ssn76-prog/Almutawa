"""Student protection, wellbeing, inclusion, and confidence environment.

Internal decision-support only. It does not diagnose mental-health conditions,
read private intent, impose punishment, or replace authorized school/family/
professional safeguarding decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    NORMAL = "normal"
    SUPPORT = "support"
    ELEVATED = "elevated"
    SAFETY = "safety"


@dataclass(frozen=True)
class StudentContext:
    description: str
    bullying_reported: bool = False
    repeated_pattern: bool = False
    power_imbalance: bool = False
    threat_reported: bool = False
    immediate_danger: bool = False
    emotional_distress_reported: bool = False
    persistent_wellbeing_concern: bool = False
    disability_or_access_need: bool = False
    accessibility_barrier: bool = False
    discrimination_reported: bool = False
    family_safety_concern: bool = False
    teacher_is_subject_of_complaint: bool = False
    teacher_response_failed: bool = False
    complaint_in_good_faith: bool = False
    retaliation_reported: bool = False
    privacy_risk: bool = False
    safe_adult_available: bool = True
    confidence_training_requested: bool = False
    boundary_phrase_practiced: bool = False
    safe_exit_strategy_practiced: bool = False
    help_seeking_practiced: bool = False
    trusted_adults_identified: bool = False


@dataclass(frozen=True)
class ProtectionDecision:
    risk_level: RiskLevel
    student_welfare_priority: bool = True
    automatic_punishment_allowed: bool = False
    diagnosis_allowed: bool = False
    retaliation_allowed: bool = False
    admin_escalation_required: bool = False
    independent_review_required: bool = False
    follow_up_required: bool = False
    guardian_contact_requires_safeguarding_judgment: bool = False
    confidence_support_required: bool = False
    recommended_actions: tuple[str, ...] = field(default_factory=tuple)
    rights_checks: tuple[str, ...] = field(default_factory=tuple)
    known_limits: tuple[str, ...] = field(default_factory=tuple)


def evaluate(context: StudentContext) -> ProtectionDecision:
    if not context.description.strip():
        raise ValueError("description is required")

    actions: list[str] = []
    rights: list[str] = [
        "Protect dignity and privacy.",
        "Do not infer guilt from an allegation alone.",
        "Do not retaliate against a good-faith report.",
        "Do not treat disability, distress, or learning need as misconduct.",
    ]
    limits = [
        "The system cannot read thoughts or private intent.",
        "The system is decision-support and cannot replace authorized human safeguarding review.",
        "Mental-health signals are support indicators, not diagnoses.",
    ]

    risk = RiskLevel.NORMAL
    admin = False
    independent = False
    follow_up = False
    guardian_safeguarding = False
    confidence_support = context.confidence_training_requested

    # Safety gate always comes first.
    if context.immediate_danger or context.threat_reported:
        risk = RiskLevel.SAFETY
        admin = True
        follow_up = True
        actions.append("Move the student to a safe supervised setting and notify an authorized responsible adult immediately.")

    # Bullying pattern gate.
    bullying_pattern = context.bullying_reported and (
        context.repeated_pattern or context.power_imbalance
    )
    if bullying_pattern:
        risk = max(risk, RiskLevel.ELEVATED, key=lambda value: list(RiskLevel).index(value))
        follow_up = True
        confidence_support = True
        actions.append("Stop the harmful behavior, document facts, hear parties fairly, and follow up until recurrence risk is addressed.")

    # Escalate when the teacher cannot impartially resolve the case.
    if context.teacher_response_failed or context.teacher_is_subject_of_complaint:
        admin = True
        independent = True
        actions.append("Escalate to an administrator or independent reviewer; the complained-about teacher must not be the sole decision-maker.")

    # Wellbeing support without diagnosis.
    if context.emotional_distress_reported or context.persistent_wellbeing_concern:
        risk = max(risk, RiskLevel.SUPPORT, key=lambda value: list(RiskLevel).index(value))
        follow_up = True
        actions.append("Provide a calm listening space and coordinate appropriate school/family/professional support without diagnosing.")

    # Inclusion and accessibility.
    if context.disability_or_access_need or context.accessibility_barrier:
        actions.append("Identify and provide reasonable access/support adjustments so the student can participate with dignity.")
    if context.accessibility_barrier or context.discrimination_reported:
        admin = True
        independent = independent or context.discrimination_reported
        follow_up = True
        actions.append("Review the access or discrimination concern through an impartial authorized process.")

    # Family safeguarding exception.
    if context.family_safety_concern:
        admin = True
        independent = True
        follow_up = True
        guardian_safeguarding = True
        rights.append("Do not automatically contact a guardian when the family may be part of the reported safety concern.")
        actions.append("Use the authorized safeguarding route to decide safe family involvement.")

    # Anti-retaliation and privacy are global.
    if context.complaint_in_good_faith or context.retaliation_reported:
        follow_up = True
        rights.append("Monitor for retaliation after reporting and keep the case open if retaliation is reported.")
    if context.privacy_risk:
        rights.append("Share case information only with people who need it for protection, review, or support.")

    # Confidence/self-protection is skill-building, never forced confrontation.
    if confidence_support:
        actions.append("Practice clear boundaries, safe exit, factual reporting, and help-seeking; never train retaliation or forced confrontation.")
        if not context.safe_adult_available:
            admin = True
            actions.append("Identify a trusted supervised adult the student can approach.")

    if risk == RiskLevel.NORMAL and (follow_up or admin or confidence_support):
        risk = RiskLevel.SUPPORT

    return ProtectionDecision(
        risk_level=risk,
        admin_escalation_required=admin,
        independent_review_required=independent,
        follow_up_required=follow_up,
        guardian_contact_requires_safeguarding_judgment=guardian_safeguarding,
        confidence_support_required=confidence_support,
        recommended_actions=tuple(dict.fromkeys(actions)),
        rights_checks=tuple(dict.fromkeys(rights)),
        known_limits=tuple(limits),
    )
