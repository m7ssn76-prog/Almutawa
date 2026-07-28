from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["draft", "reviewed", "approved", "archived"]


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1, max_length=20000)
    status: Status = "draft"


class KnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=20000)
    status: Status | None = None


class KnowledgeItem(BaseModel):
    id: int
    title: str
    content: str
    status: Status
    created_at: str
    updated_at: str
