#!/usr/bin/env python3
"""Smart Education System v4.0 — GitHub environment entry point.

Student welfare and safety first; no automatic punishment; no mental-health diagnosis.
This repository entry point is intentionally self-contained and network-free.
"""
from dataclasses import dataclass, asdict
import json

@dataclass
class Event:
    description: str
    bullying: bool=False
    repeated: bool=False
    power_imbalance: bool=False
    immediate_danger: bool=False
    teacher_response_failed: bool=False
    teacher_is_subject: bool=False
    emotional_distress: bool=False
    disability_or_access_need: bool=False
    confidence_training: bool=False


def evaluate(e: Event):
    high_risk = e.immediate_danger
    bullying_pattern = e.bullying and e.repeated and e.power_imbalance
    admin = high_risk or e.teacher_response_failed or e.teacher_is_subject
    return {
        "student_welfare_priority": True,
        "automatic_punishment_allowed": False,
        "bullying_level": "high_risk" if high_risk else ("likely_pattern" if bullying_pattern else ("concern" if e.bullying else "none")),
        "immediate_protection_required": high_risk,
        "admin_independent_review_required": admin,
        "wellbeing_support_required": e.emotional_distress,
        "inclusion_support_required": e.disability_or_access_need,
        "confidence_self_protection_training": e.confidence_training or bullying_pattern,
        "known_limits": ["No mind-reading or private-intent inference", "Decision support only; authorized humans retain school authority"],
    }


def self_test():
    cases = [
        (Event("normal"), lambda d: not d["automatic_punishment_allowed"]),
        (Event("bullying", bullying=True, repeated=True, power_imbalance=True), lambda d: d["bullying_level"] == "likely_pattern"),
        (Event("danger", immediate_danger=True), lambda d: d["immediate_protection_required"]),
        (Event("teacher conflict", teacher_is_subject=True), lambda d: d["admin_independent_review_required"]),
        (Event("wellbeing", emotional_distress=True), lambda d: d["wellbeing_support_required"]),
        (Event("access", disability_or_access_need=True), lambda d: d["inclusion_support_required"]),
        (Event("confidence", confidence_training=True), lambda d: d["confidence_self_protection_training"]),
    ]
    passed=sum(bool(check(evaluate(event))) for event,check in cases)
    return {"passed":passed,"total":len(cases),"all_passed":passed==len(cases)}

if __name__ == "__main__":
    print(json.dumps({"name":"Smart Education System v4.0","status":"ready_github_internal_test","tests":self_test()}, indent=2))
