from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

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
EvidenceAnswerStatus = Literal["answered", "insufficient_evidence"]


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1, max_length=20000)
    status: Status = "draft"
    source_type: SourceType = "text"
    purpose: str = Field(default="knowledge_management", min_length=3, max_length=200)
    sensitivity: Sensitivity = "internal"
    transformation_state: TransformationState = "original"


class KnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=20000)
    status: Status | None = None
    source_type: SourceType | None = None
    purpose: str | None = Field(default=None, min_length=3, max_length=200)
    sensitivity: Sensitivity | None = None
    transformation_state: TransformationState | None = None


class KnowledgeItem(BaseModel):
    id: int
    title: str
    content: str
    status: Status
    source_type: SourceType
    purpose: str
    sensitivity: Sensitivity
    transformation_state: TransformationState
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
