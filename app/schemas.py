from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .anti_fabrication import render_claims

# Pre-pilot API states only. "approved" is intentionally excluded until
# authenticated RBAC and an authorized approval workflow are implemented.
Status = Literal["draft", "reviewed", "archived"]
SourceType = Literal["text", "audio_transcript", "ocr_text", "translation", "file_text"]
Sensitivity = Literal["public", "internal", "sensitive", "restricted"]
TransformationState = Literal[
    "original",
    "verified_against_original",
    "uncertain",
    "conflict",
]
InputDataOrigin = Literal["synthetic", "public", "approved_low_sensitivity"]
DataOrigin = Literal[
    "synthetic",
    "public",
    "approved_low_sensitivity",
    "unverified_legacy",
]
ProvenanceVersion = Literal["legacy-v0", "canonical-json-v1"]
EvidenceAnswerStatus = Literal["answered", "insufficient_evidence"]
ClaimStatus = Literal["verified", "inference", "unverified", "conflict"]

_EXECUTION_CLAIM_RE = re.compile(
    r"(?:\b(?:implemented|executed|merged|deployed|connected|passed|succeeded|successful|running|production)\b|"
    r"(?:تم|نُفذ|نفذ|اشتغل|شغّال|نجح|دُمج|دمج|نشر|متصل|تشغيل|إنتاجي))",
    re.IGNORECASE,
)


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1, max_length=20000)
    status: Status = "draft"
    source_type: SourceType = "text"
    purpose: str = Field(default="knowledge_management", min_length=3, max_length=200)
    sensitivity: Sensitivity = "internal"
    transformation_state: TransformationState = "original"
    data_origin: InputDataOrigin = "synthetic"
    approval_reference: str | None = Field(default=None, min_length=3, max_length=200)

    @model_validator(mode="after")
    def validate_public_safe_origin(self) -> "KnowledgeCreate":
        if self.data_origin == "approved_low_sensitivity" and not self.approval_reference:
            raise ValueError(
                "approval_reference is required for approved_low_sensitivity data"
            )
        if self.data_origin != "approved_low_sensitivity" and self.approval_reference is not None:
            raise ValueError(
                "approval_reference is only allowed for approved_low_sensitivity data"
            )
        return self


class KnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=20000)
    status: Status | None = None
    source_type: SourceType | None = None
    purpose: str | None = Field(default=None, min_length=3, max_length=200)
    sensitivity: Sensitivity | None = None
    transformation_state: TransformationState | None = None
    data_origin: InputDataOrigin | None = None
    approval_reference: str | None = Field(default=None, min_length=3, max_length=200)


class KnowledgeItem(BaseModel):
    id: int
    title: str
    content: str
    status: Status
    source_type: SourceType
    purpose: str
    sensitivity: Sensitivity
    transformation_state: TransformationState
    data_origin: DataOrigin
    approval_reference: str | None
    provenance_hash: str
    provenance_version: ProvenanceVersion
    created_at: str
    updated_at: str


class EvidenceQuestionRequest(BaseModel):
    q: str = Field(min_length=3, max_length=500)


class EvidenceClaim(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=1200,
        description="One atomic claim only; do not combine unrelated facts.",
    )
    status: ClaimStatus = Field(
        description="verified for direct evidence, inference for explicit reasoning, otherwise unverified/conflict."
    )
    evidence_ids: list[int] = Field(
        default_factory=list,
        max_length=10,
        description="IDs from the supplied evidence packet that support this exact claim.",
    )


class EvidenceAgentOutput(BaseModel):
    status: EvidenceAnswerStatus
    answer: str = Field(
        min_length=1,
        max_length=4000,
        description="This field is normalized server-side from claims; do not introduce facts outside claims.",
    )
    evidence_ids: list[int] = Field(default_factory=list, max_length=10)
    claims: list[EvidenceClaim] = Field(
        default_factory=list,
        max_length=12,
        description="Claim-level evidence map. Required for answered output.",
    )

    @model_validator(mode="after")
    def enforce_claim_level_grounding(self) -> "EvidenceAgentOutput":
        if self.status == "insufficient_evidence":
            self.evidence_ids = []
            self.claims = []
            self.answer = "Insufficient reviewed evidence / لا يوجد دليل مُراجع كافٍ."
            return self

        if not self.claims:
            raise ValueError("answered output requires claim-level evidence mapping")

        used: list[int] = []
        for claim in self.claims:
            if claim.status in {"unverified", "conflict"}:
                raise ValueError("answered output cannot contain unverified/conflict claims")
            if not claim.evidence_ids:
                raise ValueError("every answered claim requires evidence IDs")
            if _EXECUTION_CLAIM_RE.search(claim.text) and claim.status != "verified":
                raise ValueError("execution/state claims must be verified, not inferred")
            used.extend(claim.evidence_ids)

        # Do not trust a model-generated global citation list or wrapper prose.
        # Derive both strictly from the per-claim map.
        self.evidence_ids = list(dict.fromkeys(used))
        self.answer = render_claims(self.claims)
        return self


class EvidenceCitation(BaseModel):
    id: int
    title: str
    provenance_hash: str
    provenance_version: ProvenanceVersion


class EvidenceAnswerResponse(BaseModel):
    status: EvidenceAnswerStatus
    answer: str
    model: str | None = None
    evidence: list[EvidenceCitation] = Field(default_factory=list, max_length=10)
    claims: list[EvidenceClaim] = Field(default_factory=list, max_length=12)
