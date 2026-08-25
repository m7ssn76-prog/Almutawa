#!/usr/bin/env python3
"""Education Guard Engine v4.4 — de-escalation and protection adapter."""
from smart_education_system import Event, evaluate
import json


def guard(event: Event):
    decision = evaluate(event)
    deescalation = decision.get("de_escalation", {})
    mode = deescalation.get("mode", "monitor")

    decision["prohibited_actions"] = [
        "automatic punishment",
        "retaliation for good-faith reporting",
        "humiliation or public shaming",
        "unsafe confrontation",
        "forcing a child/student to resolve a serious safety case alone",
        "provocative escalation when a safer de-escalation path is available",
        "group confrontation or public argument when a private neutral review is safer",
        "pressuring parties to reconcile before safety and facts are established",
    ]

    decision["de_escalation_guard"] = {
        "mode": mode,
        "default_response": (
            "protect_and_separate" if mode == "safety_first" else
            "calm_private_review" if mode == "active" else
            "monitor_and_keep_language_neutral"
        ),
        "required_behaviors": [
            "use calm, neutral, non-accusatory language",
            "state verified facts separately from assumptions",
            "avoid threats, sarcasm, ridicule, and public blame",
            "reduce the audience around the conflict when safe",
            "give each party a chance to speak without interruption",
            "use one neutral mediator/reviewer when direct discussion is not productive",
            "define one clear next action instead of widening the dispute",
            "document what changed and whether tension decreased",
        ],
        "cooling_off_allowed": mode == "active",
        "cooling_off_rule": "pause nonessential discussion briefly when emotions are rising, but never delay urgent protection",
        "success_signals": [
            "no new threats or insults",
            "parties are physically and emotionally safer",
            "facts and next actions are clear",
            "no retaliation after reporting",
        ],
    }

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
        (Event("danger", immediate_danger=True), lambda d: d["de_escalation_guard"]["default_response"] == "protect_and_separate"),
        (Event("teacher subject", teacher_is_subject=True), lambda d: d["admin_independent_review_required"]),
        (Event("family concern", age_stage="child", family_safety_concern=True), lambda d: not d["guardian_involvement_safe_to_consider"]),
        (Event("wellbeing", emotional_distress=True), lambda d: d["wellbeing_support_required"]),
        (Event("access", disability_or_access_need=True), lambda d: d["inclusion_support_required"]),
        (Event("de-escalate", de_escalation_requested=True), lambda d: d["de_escalation_guard"]["default_response"] == "calm_private_review"),
        (Event("danger de-escalation", immediate_danger=True, de_escalation_requested=True), lambda d: d["de_escalation_guard"]["mode"] == "safety_first"),
        (Event("cooling off", active_argument=True, conflict_level="medium"), lambda d: d["de_escalation_guard"]["cooling_off_allowed"]),
        (Event("neutral language"), lambda d: "use calm, neutral, non-accusatory language" in d["de_escalation_guard"]["required_behaviors"]),
    ]
    results = [(guard(e), check) for e, check in cases]
    passed = sum(bool(check(result)) for result, check in results)
    return {"passed": passed, "total": len(results), "all_passed": passed == len(results)}


if __name__ == "__main__":
    print(json.dumps({"name": "Education Guard Engine v4.4", "status": "ready_github_internal_test", "tests": self_test()}, indent=2))
