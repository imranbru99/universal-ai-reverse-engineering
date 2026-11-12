from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = ""
    organization_name: str = Field(min_length=2, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str

    model_config = {"from_attributes": True}


class OrgOut(BaseModel):
    id: UUID
    name: str
    slug: str
    kill_switch: bool

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = ""
    target_name: str = "Primary target"
    target_url: str
    authorization_declaration: str = Field(min_length=20)
    allowlist_domains: list[str]
    path_prefixes: list[str] = Field(default_factory=lambda: ["/"])
    max_depth: int = 4
    max_pages: int = 40
    max_minutes: int = 10
    allow_authenticated: bool = False


class ProjectOut(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: str
    status: str
    kill_switch: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScopeOut(BaseModel):
    id: UUID
    allowlist_domains: list[str]
    path_prefixes: list[str]
    max_depth: int
    max_pages: int
    max_minutes: int
    allow_authenticated: bool
    declaration_text: str

    model_config = {"from_attributes": True}


class AnalysisRunOut(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    current_stage: str
    stage_state: dict[str, Any]
    budgets: dict[str, Any]
    error_message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ScreenStateOut(BaseModel):
    id: UUID
    fingerprint: str
    url: str
    title: str
    auth_state: str
    viewport: str
    components: list[Any]
    confidence: float
    completeness: str
    classification: str
    screenshot_key: str

    model_config = {"from_attributes": True}


class TransitionOut(BaseModel):
    id: UUID
    from_state_id: UUID | None
    to_state_id: UUID | None
    trigger: str
    skipped_reason: str
    inputs: dict[str, Any]

    model_config = {"from_attributes": True}


class ClaimOut(BaseModel):
    id: UUID
    content: str
    classification: str
    confidence: float
    rationale: str
    review_status: str
    open_questions: list[Any]

    model_config = {"from_attributes": True}


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject", "correct"]
    correction_text: str = ""


class DomainEntityOut(BaseModel):
    id: UUID
    name: str
    description: str
    classification: str
    confidence: float
    fields: list[dict[str, Any]] = []

    model_config = {"from_attributes": True}


class ExportOut(BaseModel):
    id: UUID
    filename: str
    storage_key: str
    download_url: str
