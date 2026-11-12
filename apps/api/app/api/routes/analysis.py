from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_project_for_user
from app.config import get_settings
from app.db import get_db
from app.models import (
    AnalysisJob,
    AnalysisRun,
    AuthorizationScope,
    DomainEntity,
    DomainField,
    ExportArtifact,
    InferenceClaim,
    ReviewDecision,
    ScreenState,
    TargetApplication,
    Transition,
    User,
)
from app.models.entities import ClaimClassification, PipelineStage, RoleEnum, RunStatus
from app.schemas.api import (
    AnalysisRunOut,
    ClaimOut,
    DomainEntityOut,
    ExportOut,
    ReviewRequest,
    ScreenStateOut,
    TransitionOut,
)
from app.services.audit import audit
from app.services import storage as storage_service

router = APIRouter()


@router.post("/projects/{project_id}/analysis-runs", response_model=AnalysisRunOut)
def start_analysis(project_id: UUID, db: Session = Depends(get_db), ctx=Depends(get_project_for_user)):
    user, project, membership = ctx
    from app.api.deps import ROLE_RANK

    if ROLE_RANK[membership.role] < ROLE_RANK[RoleEnum.analyst]:
        raise HTTPException(status_code=403, detail="Analyst role required")
    if project.kill_switch:
        raise HTTPException(status_code=403, detail="Project kill switch active")

    from app.models import Organization

    org = db.get(Organization, project.organization_id)
    if org and org.kill_switch:
        raise HTTPException(status_code=403, detail="Organization kill switch active")

    scope = db.scalar(
        select(AuthorizationScope)
        .where(AuthorizationScope.project_id == project.id)
        .order_by(AuthorizationScope.created_at.desc())
    )
    if not scope:
        raise HTTPException(status_code=400, detail="Authorization scope required")

    target = db.scalar(select(TargetApplication).where(TargetApplication.project_id == project.id))
    if not target:
        raise HTTPException(status_code=400, detail="Target application required")

    run = AnalysisRun(
        project_id=project.id,
        organization_id=project.organization_id,
        status=RunStatus.pending,
        current_stage=PipelineStage.A_INTAKE,
        stage_state={"completed_stages": []},
        budgets={
            "max_depth": scope.max_depth,
            "max_pages": scope.max_pages,
            "max_minutes": scope.max_minutes,
        },
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()
    job = AnalysisJob(
        run_id=run.id,
        organization_id=project.organization_id,
        job_type="pipeline",
        status="queued",
    )
    db.add(job)
    audit(
        db,
        action="analysis.start",
        organization_id=project.organization_id,
        actor_user_id=user.id,
        resource_type="analysis_run",
        resource_id=str(run.id),
    )
    db.commit()

    # Enqueue celery task
    from workers.tasks.pipeline import run_analysis_pipeline

    async_result = run_analysis_pipeline.delay(str(run.id))
    job.celery_task_id = async_result.id
    job.status = "started"
    db.commit()
    db.refresh(run)
    return run


@router.get("/analysis-runs/{run_id}", response_model=AnalysisRunOut)
def get_run(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = _get_run_for_user(db, user, run_id)
    return run


@router.get("/analysis-runs/{run_id}/states", response_model=list[ScreenStateOut])
def list_states(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = _get_run_for_user(db, user, run_id)
    return db.scalars(select(ScreenState).where(ScreenState.run_id == run.id)).all()


@router.get("/analysis-runs/{run_id}/transitions", response_model=list[TransitionOut])
def list_transitions(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = _get_run_for_user(db, user, run_id)
    return db.scalars(select(Transition).where(Transition.run_id == run.id)).all()


@router.get("/analysis-runs/{run_id}/claims", response_model=list[ClaimOut])
def list_claims(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = _get_run_for_user(db, user, run_id)
    return db.scalars(select(InferenceClaim).where(InferenceClaim.run_id == run.id)).all()


@router.get("/analysis-runs/{run_id}/entities", response_model=list[DomainEntityOut])
def list_entities(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = _get_run_for_user(db, user, run_id)
    entities = db.scalars(
        select(DomainEntity)
        .where(DomainEntity.run_id == run.id)
        .options(selectinload(DomainEntity.fields))
    ).all()
    out: list[DomainEntityOut] = []
    for e in entities:
        out.append(
            DomainEntityOut(
                id=e.id,
                name=e.name,
                description=e.description,
                classification=e.classification if isinstance(e.classification, str) else e.classification.value,
                confidence=e.confidence,
                fields=[
                    {
                        "id": str(f.id),
                        "name": f.name,
                        "data_type": f.data_type,
                        "nullable": f.nullable,
                        "classification": f.classification
                        if isinstance(f.classification, str)
                        else f.classification.value,
                    }
                    for f in e.fields
                ],
            )
        )
    return out


@router.post("/claims/{claim_id}/review", response_model=ClaimOut)
def review_claim(
    claim_id: UUID,
    body: ReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.get(InferenceClaim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    _get_run_for_user(db, user, claim.run_id)

    decision = ReviewDecision(
        claim_id=claim.id,
        organization_id=claim.organization_id,
        reviewer_user_id=user.id,
        decision=body.decision,
        correction_text=body.correction_text,
    )
    db.add(decision)
    claim.review_status = body.decision
    if body.decision == "approve":
        claim.classification = ClaimClassification.USER_CONFIRMED
    elif body.decision == "correct" and body.correction_text:
        claim.content = body.correction_text
        claim.classification = ClaimClassification.USER_CONFIRMED
    audit(
        db,
        action="claim.review",
        organization_id=claim.organization_id,
        actor_user_id=user.id,
        resource_type="inference_claim",
        resource_id=str(claim.id),
        detail={"decision": body.decision},
    )
    db.commit()
    db.refresh(claim)
    return claim


@router.post("/analysis-runs/{run_id}/generate", response_model=AnalysisRunOut)
def generate(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = _get_run_for_user(db, user, run_id)
    pending = db.scalars(
        select(InferenceClaim).where(
            InferenceClaim.run_id == run.id,
            InferenceClaim.review_status == "pending",
            InferenceClaim.confidence < 0.75,
        )
    ).all()
    # Allow generation if critical claims reviewed OR user forces after G stage
    if run.current_stage not in {
        PipelineStage.G_REVIEW,
        PipelineStage.H_PLAN,
        PipelineStage.O_EXPORT,
        PipelineStage.F_GAPS,
    } and run.status not in {RunStatus.awaiting_review, RunStatus.completed}:
        # still allow if modeling done
        completed = set(run.stage_state.get("completed_stages", []))
        if "E_MODELING" not in completed and "F_GAPS" not in completed:
            raise HTTPException(status_code=400, detail="Analysis has not reached review/generation stage")

    from workers.tasks.pipeline import run_generation_pipeline

    run.status = RunStatus.generating
    db.commit()
    run_generation_pipeline.delay(str(run.id))
    audit(
        db,
        action="generation.start",
        organization_id=run.organization_id,
        actor_user_id=user.id,
        resource_type="analysis_run",
        resource_id=str(run.id),
        detail={"pending_low_confidence_claims": len(pending)},
    )
    db.commit()
    db.refresh(run)
    return run


@router.get("/analysis-runs/{run_id}/export", response_model=ExportOut)
def get_export(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = _get_run_for_user(db, user, run_id)
    export = db.scalar(
        select(ExportArtifact)
        .where(ExportArtifact.run_id == run.id)
        .order_by(ExportArtifact.created_at.desc())
    )
    if not export:
        raise HTTPException(status_code=404, detail="Export not ready")
    settings = get_settings()
    return ExportOut(
        id=export.id,
        filename=export.filename,
        storage_key=export.storage_key,
        download_url=f"{settings.api_public_url}/api/v1/exports/{export.id}/download",
    )


@router.get("/exports/{export_id}/download")
def download_export(export_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    export = db.get(ExportArtifact, export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    _get_run_for_user(db, user, export.run_id)
    # Prefer local file mirror for demo reliability
    local = storage_service.local_export_path(export.filename)
    if local.exists():
        return FileResponse(local, filename=export.filename, media_type="application/zip")
    data = storage_service.get_bytes(export.storage_key)
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
    )


def _get_run_for_user(db: Session, user: User, run_id: UUID) -> AnalysisRun:
    from app.models import Membership

    run = db.get(AnalysisRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == run.organization_id,
            Membership.user_id == user.id,
        )
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return run
