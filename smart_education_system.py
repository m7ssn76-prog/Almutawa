#!/usr/bin/env python3
"""Smart Education System v4.4 — internal decision-support entry point.

Safety, dignity, inclusion and evidence remain mandatory. The sustainability gate now also
checks capacity, occupancy, workforce and facility/rental-cost pressure so inclusion does not
silently become an unsafe or financially unsupported expansion.
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
    capacity_planning_context: bool = False
    expected_demand: int = 0
    available_capacity: int = 0
    planned_staff: int = 0
    required_staff: int = 0
    rental_cost: float = 0.0
    workforce_cost: float = 0.0
    equipment_cost: float = 0.0
    operating_budget: float = 0.0


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
        actions += ["prioritize immediate protection before dialogue", "separate parties safely when appropriate", "use calm neutral language", "escalate to an authorized safeguarding/admin reviewer"]
    elif mode == "active":
        actions += ["reduce provocative wording", "separate verified facts from interpretations", "let each party speak when safe", "focus on the immediate issue", "use a neutral reviewer when needed", "define one clear next action"]
    return {"mode": mode, "required": mode in {"active", "safety_first"}, "actions": actions, "principles": ["de-escalation does not cancel safety duties", "verify before blame", "no retaliation or humiliation"]}


def _capacity_cost_gate(e: Event) -> dict:
    if not e.capacity_planning_context:
        return {"active": False, "status": "not_applicable", "actions": []}
    numeric = [e.expected_demand, e.available_capacity, e.planned_staff, e.required_staff, e.rental_cost, e.workforce_cost, e.equipment_cost, e.operating_budget]
    if any(value < 0 for value in numeric):
        raise ValueError("capacity and cost inputs cannot be negative")
    total_cost = e.rental_cost + e.workforce_cost + e.equipment_cost
    occupancy = (e.expected_demand / e.available_capacity) if e.available_capacity else None
    gaps = []
    if e.available_capacity == 0 or e.expected_demand > e.available_capacity:
        gaps.append("capacity_shortfall")
    if e.required_staff > e.planned_staff:
        gaps.append("workforce_shortfall")
    if e.operating_budget == 0 or total_cost > e.operating_budget:
        gaps.append("budget_pressure")
    actions = []
    if "capacity_shortfall" in gaps:
        actions.append("rebalance time slots, space and demand before adding permanent capacity")
    if "workforce_shortfall" in gaps:
        actions.append("align safe staffing with expected demand before expanding service")
    if "budget_pressure" in gaps:
        actions.append("compare rental, workforce and equipment cost against approved operating budget")
    return {
        "active": True,
        "status": "review_required" if gaps else "within_plan",
        "expected_demand": e.expected_demand,
        "available_capacity": e.available_capacity,
        "occupancy_ratio": occupancy,
        "planned_staff": e.planned_staff,
        "required_staff": e.required_staff,
        "total_planned_cost": total_cost,
        "operating_budget": e.operating_budget,
        "gaps": gaps,
        "actions": actions,
        "principles": ["never reduce safeguarding to cut cost", "optimize existing capacity before expansion", "measure cost per served case only from actual data", "do not claim savings before baseline and measured results"],
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
    return {"active": True, "status": "ready" if not gaps else "review_required", "actions": gaps, "principles": ["understand before judging", "preserve provenance", "protect dignity privacy inclusion and accessibility", "seek sustainable measurable benefit"], "official_haramain_affiliation_claimed": False}


def evaluate(e: Event):
    if not e.description.strip():
        raise ValueError("description is required")
    if e.actor_role not in VALID_ROLES or e.target_role not in VALID_ROLES:
        raise ValueError("invalid role")
    if e.age_stage not in VALID_STAGES or e.conflict_level not in VALID_CONFLICT_LEVELS:
        raise ValueError("invalid context")
    context = learner_context(e)
    high_risk = e.immediate_danger or e.threat or e.physical_harm
    bullying_pattern = e.bullying and e.repeated and e.power_imbalance
    admin = high_risk or e.teacher_response_failed or e.teacher_is_subject or e.family_safety_concern
    guardian_safe = context in {"child_student", "school_student"} and not e.family_safety_concern
    rights = ["student/child welfare and safety are prioritized with fair process", "no automatic guilt or punishment based only on an allegation"]
    actions = []
    if context == "child_student":
        rights += ["apply child-safeguarding and educational rights together", "use age-appropriate language"]
        actions.append("coordinate support with a safe responsible adult when appropriate")
    if high_risk:
        actions += ["stop unsafe behavior", "move affected learner to a safer supervised setting", "escalate to authorized safeguarding/admin staff"]
    if e.family_safety_concern:
        rights.append("do not automatically contact a potentially implicated guardian")
        actions.append("route contact decisions through an authorized safeguarding reviewer")
    elif guardian_safe and (high_risk or bullying_pattern or e.emotional_distress):
        actions.append("consider safe guardian involvement according to policy")
    if e.emotional_distress:
        actions.append("offer wellbeing support without diagnosing a mental-health condition")
    if e.disability_or_access_need:
        actions.append("provide inclusion/access support without reducing dignity or credibility")
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
        "de_escalation": _de_escalation_plan(e, high_risk, bullying_pattern),
        "knowledge_to_service": _knowledge_service_gate(e),
        "capacity_and_cost": _capacity_cost_gate(e),
        "rights_checks": rights,
        "recommended_actions": actions,
        "known_limits": ["No mind-reading", "Wellbeing signals are not diagnoses", "Authorized humans retain authority", "No official Haramain affiliation is inferred", "Cost savings require measured baseline evidence"],
    }


def self_test():
    cases = [
        (Event("normal"), lambda d: not d["automatic_punishment_allowed"]),
        (Event("child", age_stage="child"), lambda d: d["learner_context"] == "child_student"),
        (Event("bullying", bullying=True, repeated=True, power_imbalance=True), lambda d: d["bullying_level"] == "likely_pattern"),
        (Event("danger", immediate_danger=True), lambda d: d["immediate_protection_required"]),
        (Event("de-escalate", de_escalation_requested=True), lambda d: d["de_escalation"]["mode"] == "active"),
        (Event("knowledge", knowledge_service_context=True), lambda d: d["knowledge_to_service"]["status"] == "review_required"),
        (Event("service ready", knowledge_service_context=True, evidence_verified=True, community_benefit=True, sustainability_considered=True), lambda d: d["knowledge_to_service"]["status"] == "ready"),
        (Event("capacity ok", capacity_planning_context=True, expected_demand=80, available_capacity=100, planned_staff=10, required_staff=8, rental_cost=1000, workforce_cost=2000, equipment_cost=500, operating_budget=4000), lambda d: d["capacity_and_cost"]["status"] == "within_plan"),
        (Event("capacity pressure", capacity_planning_context=True, expected_demand=120, available_capacity=100, planned_staff=7, required_staff=10, rental_cost=2000, workforce_cost=3000, equipment_cost=1000, operating_budget=5000), lambda d: set(d["capacity_and_cost"]["gaps"]) == {"capacity_shortfall", "workforce_shortfall", "budget_pressure"}),
        (Event("safety despite cost", capacity_planning_context=True, immediate_danger=True, operating_budget=1), lambda d: d["immediate_protection_required"] and "never reduce safeguarding to cut cost" in d["capacity_and_cost"]["principles"]),
    ]
    passed = sum(bool(check(evaluate(event))) for event, check in cases)
    return {"passed": passed, "total": len(cases), "all_passed": passed == len(cases)}


if __name__ == "__main__":
    print(json.dumps({"name": "Smart Education System v4.4", "status": "ready_github_internal_test", "tests": self_test()}, indent=2))
