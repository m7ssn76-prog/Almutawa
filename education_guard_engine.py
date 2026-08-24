#!/usr/bin/env python3
"""Education Guard Engine v4.0 — protection adapter for Smart Education System."""
from smart_education_system import Event, evaluate
import json

def guard(event: Event):
    decision=evaluate(event)
    decision["prohibited_actions"]=["automatic punishment","retaliation for good-faith reporting","humiliation","unsafe confrontation"]
    decision["escalation_chain"]=["teacher when appropriate","counselor/reviewer","admin/independent reviewer when required","guardian when safe and appropriate"]
    return decision

def self_test():
    cases=[
        Event("bullying",bullying=True,repeated=True,power_imbalance=True),
        Event("danger",immediate_danger=True),
        Event("teacher subject",teacher_is_subject=True),
        Event("wellbeing",emotional_distress=True),
        Event("access",disability_or_access_need=True),
    ]
    results=[guard(c) for c in cases]
    ok=(results[0]["bullying_level"]=="likely_pattern" and results[1]["immediate_protection_required"] and results[2]["admin_independent_review_required"] and results[3]["wellbeing_support_required"] and results[4]["inclusion_support_required"] and all(not r["automatic_punishment_allowed"] for r in results))
    return {"passed":5 if ok else 0,"total":5,"all_passed":ok}

if __name__=="__main__":
    print(json.dumps({"name":"Education Guard Engine v4.0","status":"ready_github_internal_test","tests":self_test()},indent=2))
