#!/usr/bin/env python3
"""Smart Education System v4.1 — GitHub environment entry point.

Student/child welfare and safety first. No automatic punishment. No mental-health diagnosis.
This repository entry point is self-contained and network-free.
"""
from dataclasses import dataclass
import json

VALID_ROLES = {"student", "teacher", "counselor", "admin", "guardian", "reviewer", "staff", "unknown"}
VALID_STAGES = {"child", "teen", "adult", "unknown"}


@dataclass
class Event:
    description: str
    actor_role: str = "student"
    target_role: str = "student"
    age_stage: str = "teen"
    bullying: bool = False
    repeated: bool = False
    power_imbalance: bool = False
    immediate_danger: bool = False
    threat: bool = False
    physical_harm: bool = False
    teacher_response_failed: bool = False
    teacher_is_subject: bool = False
    emotional_distress: bool = False
    disability_or_access_need: bool = False
    family_safety_concern: bool = False
    safe_adult_available: bool = False
    confidence_training: bool = False


def learner_context(e: Event) -> str:
    student_involved = e.actor_role == "student" or e.target_role == "student"
    if e.age_stage == "child" and student_involved:
        return "child_student"
    if e.age_stage == "child":
        return "child"
    if student_involved and e.age_stage in {"teen", "unknown"}:
        return "school_student"
    if student_involved and e.age_stage == "adult":
        return "adult_learner"
    return "unknown"


def evaluate(e: Event):
    if not e.description.strip():
        raise ValueError("description is required")
    if e.actor_role not in VALID_ROLES or e.target_role not in VALID_ROLES:
        raise ValueError("invalid role")
    if e.age_stage not in VALID_STAGES:
        raise ValueError("invalid age_stage")

    context = learner_context(e)
    high_risk = e.immediate_danger or e.threat or e.physical_harm
    bullying_pattern = e.bullying and e.repeated and e.power_imbalance
    admin = high_risk or e.teacher_response_failed or e.teacher_is_subject or e.family_safety_concern
    guardian_safe = context in {"child_student", "school_student"} and not e.family_safety_concern

    rights = [
        "student/child welfare and safety are prioritized with fair process for all parties",
        "no automatic guilt or punishment based only on an allegation",
    ]
    actions = []

    if context == "child_student":
        rights += [
            "apply child-safeguarding and educational rights together",
            "use age-appropriate language and do not place adult-level responsibility on the child",
        ]
        actions.append("coordinate school support with a safe responsible adult when appropriate")
    elif context == "child":
        rights.append("apply child-safeguarding protections even outside a formal classroom context")
    elif context == "school_student":
        rights.append("preserve educational participation, dignity, and access to school support")

    if high_risk:
        actions += ["stop unsafe behavior", "move the affected child/student to a safer supervised setting", "escalate to authorized school safeguarding/admin staff"]
    if e.family_safety_concern:
        rights.append("do not automatically contact a potentially implicated guardian")
        actions.append("route guardian/contact decisions through an authorized safeguarding reviewer")
    elif guardian_safe and (high_risk or bullying_pattern or e.emotional_distress):
        actions.append("consider safe guardian involvement according to school policy")
    if e.emotional_distress:
        actions.append("offer wellbeing support without diagnosing or labeling a mental-health condition")
    if e.disability_or_access_need:
        actions.append("provide appropriate inclusion/access support without reducing the learner's dignity or credibility")

    return {
        "learner_context": context,
        "student_welfare_priority": True,
        "automatic_punishment_allowed": False,
        "bullying_level": "high_risk" if high_risk else ("likely_pattern" if bullying_pattern else ("concern" if e.bullying else "none")),
        "immediate_protection_required": high_risk,
        "admin_independent_review_required": admin,
        "guardian_involvement_safe_to_consider": guardian_safe,
        "wellbeing_support_required": e.emotional_distress,
        "inclusion_support_required": e.disability_or_access_need,
        "confidence_self_protection_training": e.confidence_training or bullying_pattern,
        "rights_checks": rights,
        "recommended_actions": actions,
        "known_limits": [
            "No mind-reading or private-intent inference",
            "Wellbeing signals are not clinical diagnoses",
            "Decision support only; authorized humans retain school authority",
        ],
    }


def self_test():
    cases = [
        (Event("normal"), lambda d: not d["automatic_punishment_allowed"]),
        (Event("child student", age_stage="child"), lambda d: d["learner_context"] == "child_student"),
        (Event("teen student", age_stage="teen"), lambda d: d["learner_context"] == "school_student"),
        (Event("bullying", bullying=True, repeated=True, power_imbalance=True), lambda d: d["bullying_level"] == "likely_pattern"),
        (Event("danger", immediate_danger=True), lambda d: d["immediate_protection_required"]),
        (Event("teacher conflict", teacher_is_subject=True), lambda d: d["admin_independent_review_required"]),
        (Event("wellbeing", emotional_distress=True), lambda d: d["wellbeing_support_required"]),
        (Event("access", disability_or_access_need=True), lambda d: d["inclusion_support_required"]),
        (Event("family safety", age_stage="child", family_safety_concern=True), lambda d: not d["guardian_involvement_safe_to_consider"]),
        (Event("confidence", confidence_training=True), lambda d: d["confidence_self_protection_training"]),
    ]
    passed = sum(bool(check(evaluate(event))) for event, check in cases)
    return {"passed": passed, "total": len(cases), "all_passed": passed == len(cases)}


if __name__ == "__main__":
    print(json.dumps({"name": "Smart Education System v4.1", "status": "ready_github_internal_test", "tests": self_test()}, indent=2))
