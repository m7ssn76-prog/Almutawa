#!/usr/bin/env python3
"""Smart Education System v4.3 — GitHub environment entry point.

Student/child welfare and safety first. No automatic punishment. No mental-health diagnosis.
Includes de-escalation and a knowledge-to-service values gate: knowledge should become ethical,
respectful, sustainable benefit while preserving evidence, safety, dignity, inclusion and authority.
This is an internal decision-support implementation, not an official Haramain program claim.
"""
from dataclasses import dataclass
import json

VALID_ROLES = {"student", "teacher", "counselor", "admin", "guardian", "reviewer", "staff", "unknown"}
VALID_STAGES = {"child", "teen", "adult", "unknown"}
VALID_CONFLICT_LEVELS = {"none", "low", "medium", "high"}


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
    de_escalation_requested: bool = False
    active_argument: bool = False
    conflict_level: str = "none"
    knowledge_service_context: bool = False
    evidence_verified: bool = False
    community_benefit: bool = False
    sustainability_considered: bool = False


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


def _de_escalation_plan(e: Event, high_risk: bool, bullying_pattern: bool) -> dict:
    requested = e.de_escalation_requested or e.active_argument or e.conflict_level in {"medium", "high"}
    relevant = requested or e.bullying or bullying_pattern or e.emotional_distress
    mode = "safety_first" if high_risk else ("active" if relevant else "monitor")
    actions = []
    if mode == "safety_first":
        actions += [
            "prioritize immediate protection before dialogue",
            "separate the parties safely when appropriate",
            "use calm neutral language and avoid provocative exchanges",
            "escalate to an authorized safeguarding/admin reviewer",
        ]
    elif mode == "active":
        actions += [
            "reduce accusatory or provocative wording",
            "separate verified facts from interpretations and assumptions",
            "let each party speak without interruption when safe",
            "focus on the immediate issue and avoid widening the dispute",
            "use a neutral teacher/counselor/reviewer if direct discussion is not productive",
            "pause nonessential confrontation and define one clear next action",
        ]
    return {
        "mode": mode,
        "required": mode in {"active", "safety_first"},
        "actions": actions,
        "principles": [
            "de-escalation does not cancel safety duties",
            "de-escalation does not mean ignoring misconduct",
            "no retaliation, humiliation, threats, or pressure to reconcile unsafely",
            "verify before blame and preserve dignity for all parties",
        ],
    }


def _knowledge_service_gate(e: Event) -> dict:
    if not e.knowledge_service_context:
        return {"active": False, "status": "not_applicable", "actions": []}
    gaps = []
    if not e.evidence_verified:
        gaps.append("verify knowledge/evidence before presenting claims as fact")
    if not e.community_benefit:
        gaps.append("define a concrete human/community benefit")
    if not e.sustainability_considered:
        gaps.append("assess sustainability and continuity of benefit")
    return {
        "active": True,
        "status": "ready" if not gaps else "review_required",
        "actions": gaps,
        "principles": [
            "understand before judging",
            "use verified knowledge and preserve provenance",
            "translate knowledge into ethical and respectful service",
            "protect dignity, privacy, inclusion and accessibility",
            "prefer de-escalation while preserving safety and rights",
            "seek sustainable benefit rather than symbolic activity",
            "measure impact before claiming success",
        ],
        "official_haramain_affiliation_claimed": False,
    }


def evaluate(e: Event):
    if not e.description.strip():
        raise ValueError("description is required")
    if e.actor_role not in VALID_ROLES or e.target_role not in VALID_ROLES:
        raise ValueError("invalid role")
    if e.age_stage not in VALID_STAGES:
        raise ValueError("invalid age_stage")
    if e.conflict_level not in VALID_CONFLICT_LEVELS:
        raise ValueError("invalid conflict_level")

    context = learner_context(e)
    high_risk = e.immediate_danger or e.threat or e.physical_harm
    bullying_pattern = e.bullying and e.repeated and e.power_imbalance
    admin = high_risk or e.teacher_response_failed or e.teacher_is_subject or e.family_safety_concern
    guardian_safe = context in {"child_student", "school_student"} and not e.family_safety_concern
    de_escalation = _de_escalation_plan(e, high_risk, bullying_pattern)
    knowledge_service = _knowledge_service_gate(e)

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
        actions += [
            "stop unsafe behavior",
            "move the affected child/student to a safer supervised setting",
            "escalate to authorized school safeguarding/admin staff",
        ]
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
        "de_escalation": de_escalation,
        "knowledge_to_service": knowledge_service,
        "rights_checks": rights,
        "recommended_actions": actions,
        "known_limits": [
            "No mind-reading or private-intent inference",
            "Wellbeing signals are not clinical diagnoses",
            "Decision support only; authorized humans retain school authority",
            "No official Haramain affiliation or program status is inferred from this internal rule",
        ],
    }


def self_test():
    cases = [
        (Event("normal"), lambda d: not d["automatic_punishment_allowed"]),
        (Event("child student", age_stage="child"), lambda d: d["learner_context"] == "child_student"),
        (Event("bullying", bullying=True, repeated=True, power_imbalance=True), lambda d: d["bullying_level"] == "likely_pattern"),
        (Event("danger", immediate_danger=True), lambda d: d["immediate_protection_required"]),
        (Event("wellbeing", emotional_distress=True), lambda d: d["wellbeing_support_required"]),
        (Event("de-escalate", de_escalation_requested=True), lambda d: d["de_escalation"]["mode"] == "active"),
        (Event("danger de-escalation", immediate_danger=True, de_escalation_requested=True), lambda d: d["de_escalation"]["mode"] == "safety_first"),
        (Event("knowledge service", knowledge_service_context=True), lambda d: d["knowledge_to_service"]["status"] == "review_required"),
        (Event("verified service", knowledge_service_context=True, evidence_verified=True, community_benefit=True, sustainability_considered=True), lambda d: d["knowledge_to_service"]["status"] == "ready"),
        (Event("no affiliation", knowledge_service_context=True), lambda d: not d["knowledge_to_service"]["official_haramain_affiliation_claimed"]),
    ]
    passed = sum(bool(check(evaluate(event))) for event, check in cases)
    return {"passed": passed, "total": len(cases), "all_passed": passed == len(cases)}


if __name__ == "__main__":
    print(json.dumps({"name": "Smart Education System v4.3", "status": "ready_github_internal_test", "tests": self_test()}, indent=2))
