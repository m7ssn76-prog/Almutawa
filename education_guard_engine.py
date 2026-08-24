#!/usr/bin/env python3
"""Education Guard Engine v4.1 — protection adapter for Smart Education System."""
from smart_education_system import Event, evaluate
import json


def guard(event: Event):
    decision = evaluate(event)
    decision["prohibited_actions"] = [
        "automatic punishment",
        "retaliation for good-faith reporting",
        "humiliation or public shaming",
        "unsafe confrontation",
        "forcing a child/student to resolve a serious safety case alone",
    ]
    decision["escalation_chain"] = [
        "teacher when appropriate",
        "counselor/reviewer",
        "admin/independent safeguarding reviewer when required",
        "guardian only when safe and appropriate",
    ]
    return decision


def self_test():
    cases = [
        (Event("child student", age_stage="child"), lambda d: d["learner_context"] == "child_student"),
        (Event("bullying", bullying=True, repeated=True, power_imbalance=True), lambda d: d["bullying_level"] == "likely_pattern"),
        (Event("danger", immediate_danger=True), lambda d: d["immediate_protection_required"]),
        (Event("teacher subject", teacher_is_subject=True), lambda d: d["admin_independent_review_required"]),
        (Event("family concern", age_stage="child", family_safety_concern=True), lambda d: not d["guardian_involvement_safe_to_consider"]),
        (Event("wellbeing", emotional_distress=True), lambda d: d["wellbeing_support_required"]),
        (Event("access", disability_or_access_need=True), lambda d: d["inclusion_support_required"]),
    ]
    results = [(guard(e), check) for e, check in cases]
    passed = sum(bool(check(result)) for result, check in results)
    return {"passed": passed, "total": len(results), "all_passed": passed == len(results)}


if __name__ == "__main__":
    print(json.dumps({"name": "Education Guard Engine v4.1", "status": "ready_github_internal_test", "tests": self_test()}, indent=2))
