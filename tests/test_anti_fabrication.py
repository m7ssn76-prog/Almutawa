import json

import pytest
from pydantic import ValidationError

from app.anti_fabrication import render_claims, validate_claims
from app.schemas import EvidenceAgentOutput, EvidenceClaim


def test_valid_grounded_claim_passes() -> None:
    evidence = {
        7: {
            "id": 7,
            "title": "Digital environment boundary",
            "content": "The digital environment is simulation only and physical actuation is disabled.",
            "purpose": "verification",
            "provenance_hash": "a" * 64,
        }
    }
    claims = [
        {"text": "The digital environment is simulation only.", "status": "verified", "evidence_ids": [7]}
    ]

    result = validate_claims(claims, evidence)

    assert result.allowed is True
    assert result.evidence_ids == (7,)


def test_unrelated_same_language_claim_is_blocked() -> None:
    evidence = {
        3: {
            "id": 3,
            "title": "Farm state",
            "content": "Soil moisture is 48 and irrigation is off.",
            "purpose": "monitoring",
            "provenance_hash": "b" * 64,
        }
    }
    claims = [
        {"text": "The repository deployed to production successfully.", "status": "verified", "evidence_ids": [3]}
    ]

    result = validate_claims(claims, evidence)

    assert result.allowed is False


def test_execution_claim_requires_structural_run_proof() -> None:
    weak = {
        11: {
            "id": 11,
            "title": "General note",
            "content": "The workflow configuration exists in the repository.",
            "purpose": "documentation",
            "provenance_hash": "c" * 64,
        }
    }
    claim = [
        {"text": "The workflow passed successfully.", "status": "verified", "evidence_ids": [11]}
    ]

    result = validate_claims(claim, weak)

    assert result.allowed is False
    assert "run/commit" in result.reason


def test_execution_claim_accepts_github_run_commit_outcome_proof() -> None:
    proof = {
        12: {
            "id": 12,
            "title": "GitHub execution evidence",
            "content": json.dumps(
                {
                    "run_id": 32814042752,
                    "commit_sha": "90c6c1ad6a4ee84e39247fb7c4dda3d5a9ae621b",
                    "conclusion": "success",
                    "workflow": "ci",
                }
            ),
            "purpose": "execution evidence",
            "provenance_hash": "d" * 64,
        }
    }
    claim = [
        {"text": "تم تشغيل GitHub workflow ونجح.", "status": "verified", "evidence_ids": [12]}
    ]

    result = validate_claims(claim, proof)

    assert result.allowed is True
    assert result.evidence_ids == (12,)


def test_schema_rebuilds_answer_only_from_claims_and_claim_evidence() -> None:
    output = EvidenceAgentOutput(
        status="answered",
        answer="MODEL TRIED TO ADD AN UNCITED SENTENCE",
        evidence_ids=[999],
        claims=[
            EvidenceClaim(
                text="The environment is simulation only.",
                status="verified",
                evidence_ids=[4],
            ),
            EvidenceClaim(
                text="This suggests the next step should be independently verified.",
                status="inference",
                evidence_ids=[4, 5],
            ),
        ],
    )

    assert output.answer == render_claims(output.claims)
    assert "UNCITED" not in output.answer
    assert output.evidence_ids == [4, 5]


def test_schema_blocks_unverified_claim_in_answered_output() -> None:
    with pytest.raises(ValidationError):
        EvidenceAgentOutput(
            status="answered",
            answer="anything",
            evidence_ids=[1],
            claims=[
                EvidenceClaim(
                    text="Unknown claim",
                    status="unverified",
                    evidence_ids=[],
                )
            ],
        )


def test_schema_blocks_execution_claim_as_inference() -> None:
    with pytest.raises(ValidationError):
        EvidenceAgentOutput(
            status="answered",
            answer="anything",
            evidence_ids=[1],
            claims=[
                EvidenceClaim(
                    text="The workflow passed successfully.",
                    status="inference",
                    evidence_ids=[1],
                )
            ],
        )


def test_insufficient_evidence_is_normalized_fail_closed() -> None:
    output = EvidenceAgentOutput(
        status="insufficient_evidence",
        answer="Maybe it happened anyway.",
        evidence_ids=[1, 2],
        claims=[
            EvidenceClaim(text="Maybe it happened.", status="unverified", evidence_ids=[])
        ],
    )

    assert output.evidence_ids == []
    assert output.claims == []
    assert output.answer == "Insufficient reviewed evidence / لا يوجد دليل مُراجع كافٍ."
