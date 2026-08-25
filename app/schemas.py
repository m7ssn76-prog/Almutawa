from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

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
EvidenceAnswerStatus = Literal["answered", "insufficient_evidence"]


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
    created_at: str
    updated_at: str


class EvidenceAgentOutput(BaseModel):
    status: EvidenceAnswerStatus
    answer: str = Field(min_length=1, max_length=4000)
    evidence_ids: list[int] = Field(default_factory=list, max_length=10)


class EvidenceCitation(BaseModel):
    id: int
    title: str
    provenance_hash: str


class EvidenceAnswerResponse(BaseModel):
    status: EvidenceAnswerStatus
    answer: str
    model: str | None = None
    evidence: list[EvidenceCitation] = Field(default_factory=list, max_length=10)
