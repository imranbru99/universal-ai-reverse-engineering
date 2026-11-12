from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class RoleEnum(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class ClaimClassification(str, enum.Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    USER_CONFIRMED = "USER_CONFIRMED"
    UNKNOWN = "UNKNOWN"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    awaiting_review = "awaiting_review"
    generating = "generating"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class PipelineStage(str, enum.Enum):
    A_INTAKE = "A_INTAKE"
    B_SCOPE = "B_SCOPE"
    C_EVIDENCE = "C_EVIDENCE"
    D_GRAPH = "D_GRAPH"
    E_MODELING = "E_MODELING"
    F_GAPS = "F_GAPS"
    G_REVIEW = "G_REVIEW"
    H_PLAN = "H_PLAN"
    I_GENERATE = "I_GENERATE"
    J_BACKEND = "J_BACKEND"
    K_FRONTEND = "K_FRONTEND"
    L_TESTS = "L_TESTS"
    M_VISUAL = "M_VISUAL"
    N_SECURITY = "N_SECURITY"
    O_EXPORT = "O_EXPORT"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memberships: Mapped[list[Membership]] = relationship(back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    kill_switch: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memberships: Mapped[list[Membership]] = relationship(back_populates="organization")
    projects: Mapped[list[Project]] = relationship(back_populates="organization")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "organization_id", name="uq_membership"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum, name="role_enum"), default=RoleEnum.viewer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(back_populates="memberships")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    kill_switch: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped[Organization] = relationship(back_populates="projects")
    targets: Mapped[list[TargetApplication]] = relationship(back_populates="project")
    scopes: Mapped[list[AuthorizationScope]] = relationship(back_populates="project")
    evidence_items: Mapped[list[EvidenceItem]] = relationship(back_populates="project")
    analysis_runs: Mapped[list[AnalysisRun]] = relationship(back_populates="project")


class TargetApplication(Base):
    __tablename__ = "target_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    app_type: Mapped[str] = mapped_column(String(50), default="web")
    base_url: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="targets")
    versions: Mapped[list[TargetVersion]] = relationship(back_populates="target")


class TargetVersion(Base):
    __tablename__ = "target_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("target_applications.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(100), default="v1")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    target: Mapped[TargetApplication] = relationship(back_populates="versions")


class AuthorizationScope(Base):
    __tablename__ = "authorization_scopes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    declaration_text: Mapped[str] = mapped_column(Text)
    allowlist_domains: Mapped[list] = mapped_column(JSONB, default=list)
    path_prefixes: Mapped[list] = mapped_column(JSONB, default=list)
    max_depth: Mapped[int] = mapped_column(Integer, default=4)
    max_pages: Mapped[int] = mapped_column(Integer, default=40)
    max_minutes: Mapped[int] = mapped_column(Integer, default=10)
    allow_authenticated: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="scopes")


class CredentialsReference(Base):
    __tablename__ = "credentials_references"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(200))
    role_hint: Mapped[str] = mapped_column(String(100), default="")
    secret_ref: Mapped[str] = mapped_column(Text)  # encrypted blob / vault pointer
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(50))
    filename: Mapped[str] = mapped_column(String(500), default="")
    storage_key: Mapped[str] = mapped_column(String(1000))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(200), default="upload")
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="evidence_items")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus, name="run_status"), default=RunStatus.pending)
    current_stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage, name="pipeline_stage"), default=PipelineStage.A_INTAKE
    )
    stage_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    budgets: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="analysis_runs")
    jobs: Mapped[list[AnalysisJob]] = relationship(back_populates="run")
    states: Mapped[list[ScreenState]] = relationship(back_populates="run")
    transitions: Mapped[list[Transition]] = relationship(back_populates="run")
    claims: Mapped[list[InferenceClaim]] = relationship(back_populates="run")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    job_type: Mapped[str] = mapped_column(String(100))
    celery_task_id: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped[AnalysisRun] = relationship(back_populates="jobs")


class ScreenState(Base):
    __tablename__ = "screen_states"
    __table_args__ = (
        UniqueConstraint("run_id", "fingerprint", name="uq_run_fingerprint"),
        Index("ix_screen_states_run_url", "run_id", "url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    fingerprint: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(2000))
    title: Mapped[str] = mapped_column(String(500), default="")
    auth_state: Mapped[str] = mapped_column(String(50), default="anonymous")
    role: Mapped[str] = mapped_column(String(50), default="public")
    viewport: Mapped[str] = mapped_column(String(50), default="desktop")
    components: Mapped[list] = mapped_column(JSONB, default=list)
    messages: Mapped[list] = mapped_column(JSONB, default=list)
    screenshot_key: Mapped[str] = mapped_column(String(1000), default="")
    accessibility_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    completeness: Mapped[str] = mapped_column(String(50), default="partial")
    classification: Mapped[ClaimClassification] = mapped_column(
        Enum(ClaimClassification, name="claim_classification"), default=ClaimClassification.OBSERVED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped[AnalysisRun] = relationship(back_populates="states")
    component_rows: Mapped[list[ScreenComponent]] = relationship(back_populates="state")


class ScreenComponent(Base):
    __tablename__ = "screen_components"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    state_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("screen_states.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    component_type: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200), default="")
    props: Mapped[dict] = mapped_column(JSONB, default=dict)

    state: Mapped[ScreenState] = relationship(back_populates="component_rows")


class Transition(Base):
    __tablename__ = "transitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    from_state_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("screen_states.id", ondelete="SET NULL"), nullable=True
    )
    to_state_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("screen_states.id", ondelete="SET NULL"), nullable=True
    )
    trigger: Mapped[str] = mapped_column(String(200))
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    preconditions: Mapped[dict] = mapped_column(JSONB, default=dict)
    expected_effects: Mapped[dict] = mapped_column(JSONB, default=dict)
    skipped_reason: Mapped[str] = mapped_column(String(200), default="")
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped[AnalysisRun] = relationship(back_populates="transitions")


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    entry_state_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("screen_states.id"), nullable=True)
    graph: Mapped[dict] = mapped_column(JSONB, default=dict)


class ObservedApiCall(Base):
    __tablename__ = "observed_api_calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    method: Mapped[str] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(2000))
    status_code: Mapped[int] = mapped_column(Integer, default=0)
    request_headers: Mapped[dict] = mapped_column(JSONB, default=dict)
    classification: Mapped[str] = mapped_column(String(32), default=ClaimClassification.OBSERVED.value)


class ProposedApiEndpoint(Base):
    __tablename__ = "proposed_api_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    method: Mapped[str] = mapped_column(String(20))
    path: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text, default="")
    request_schema: Mapped[dict] = mapped_column(JSONB, default=dict)
    response_schema: Mapped[dict] = mapped_column(JSONB, default=dict)
    classification: Mapped[str] = mapped_column(String(32), default=ClaimClassification.INFERRED.value)


class DomainEntity(Base):
    __tablename__ = "domain_entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    classification: Mapped[str] = mapped_column(String(32), default=ClaimClassification.INFERRED.value)
    confidence: Mapped[float] = mapped_column(Float, default=0.6)

    fields: Mapped[list[DomainField]] = relationship(back_populates="entity")


class DomainField(Base):
    __tablename__ = "domain_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("domain_entities.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    data_type: Mapped[str] = mapped_column(String(100), default="string")
    nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    classification: Mapped[str] = mapped_column(String(32), default=ClaimClassification.INFERRED.value)

    entity: Mapped[DomainEntity] = relationship(back_populates="fields")


class DomainRelationship(Base):
    __tablename__ = "relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    from_entity: Mapped[str] = mapped_column(String(200))
    to_entity: Mapped[str] = mapped_column(String(200))
    relationship_type: Mapped[str] = mapped_column(String(50), default="one_to_many")
    classification: Mapped[str] = mapped_column(String(32), default=ClaimClassification.INFERRED.value)


class DesignToken(Base):
    __tablename__ = "design_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    token_type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    value: Mapped[str] = mapped_column(String(500))
    classification: Mapped[str] = mapped_column(String(32), default=ClaimClassification.INFERRED.value)


class Specification(Base):
    __tablename__ = "specifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    body_markdown: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)


class InferenceClaim(Base):
    __tablename__ = "inference_claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    classification: Mapped[ClaimClassification] = mapped_column(
        Enum(ClaimClassification, name="claim_classification", create_constraint=False),
        default=ClaimClassification.INFERRED,
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    rationale: Mapped[str] = mapped_column(Text, default="")
    environment: Mapped[dict] = mapped_column(JSONB, default=dict)
    conflicts: Mapped[list] = mapped_column(JSONB, default=list)
    open_questions: Mapped[list] = mapped_column(JSONB, default=list)
    review_status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped[AnalysisRun] = relationship(back_populates="claims")
    evidence_links: Mapped[list[ClaimEvidence]] = relationship(back_populates="claim")
    decisions: Mapped[list[ReviewDecision]] = relationship(back_populates="claim")


class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inference_claims.id", ondelete="CASCADE"), index=True)
    evidence_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evidence_items.id", ondelete="SET NULL"), nullable=True
    )
    screen_state_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("screen_states.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str] = mapped_column(Text, default="")

    claim: Mapped[InferenceClaim] = relationship(back_populates="evidence_links")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inference_claims.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(50))
    correction_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    claim: Mapped[InferenceClaim] = relationship(back_populates="decisions")


class GenerationPlan(Base):
    __tablename__ = "generation_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    target_stack: Mapped[str] = mapped_column(String(100), default="nextjs_fastapi_postgres")
    plan: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="draft")


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("generation_plans.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    path: Mapped[str] = mapped_column(String(1000))
    content_sha256: Mapped[str] = mapped_column(String(64), default="")
    storage_key: Mapped[str] = mapped_column(String(1000), default="")


class CodeArtifact(Base):
    __tablename__ = "code_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(100))
    storage_key: Mapped[str] = mapped_column(String(1000))
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(50), default="functional")
    definition: Mapped[dict] = mapped_column(JSONB, default=dict)


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    results: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VisualComparison(Base):
    __tablename__ = "visual_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    baseline_key: Mapped[str] = mapped_column(String(1000), default="")
    candidate_key: Mapped[str] = mapped_column(String(1000), default="")
    diff_percent: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, default="")


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    severity: Mapped[str] = mapped_column(String(50), default="info")
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text, default="")


class ExportArtifact(Base):
    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    storage_key: Mapped[str] = mapped_column(String(1000))
    filename: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(200))
    resource_type: Mapped[str] = mapped_column(String(100), default="")
    resource_id: Mapped[str] = mapped_column(String(100), default="")
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
