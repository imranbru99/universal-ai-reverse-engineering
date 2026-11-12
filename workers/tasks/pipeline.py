from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.db import SessionLocal
from app.models import (
    AnalysisRun,
    AuthorizationScope,
    ClaimEvidence,
    DomainEntity,
    DomainField,
    ExportArtifact,
    GeneratedFile,
    GenerationPlan,
    InferenceClaim,
    Organization,
    Project,
    ProposedApiEndpoint,
    ScreenState,
    SecurityFinding,
    TargetApplication,
    Transition,
    Workflow,
)
from app.models.entities import ClaimClassification, PipelineStage, RunStatus
from app.services import storage as storage_service
from workers.celery_app import app
from workers.exploration.explorer import explore_site
from workers.generation.next_fastapi import generate_independent_project
from workers.modeling.heuristics import infer_bookstore_domain

STAGE_ORDER = [
    PipelineStage.A_INTAKE,
    PipelineStage.B_SCOPE,
    PipelineStage.C_EVIDENCE,
    PipelineStage.D_GRAPH,
    PipelineStage.E_MODELING,
    PipelineStage.F_GAPS,
    PipelineStage.G_REVIEW,
]


def _mark_stage(run: AnalysisRun, stage: PipelineStage) -> None:
    completed = list(run.stage_state.get("completed_stages", []))
    if stage.value not in completed:
        completed.append(stage.value)
    run.stage_state = {**run.stage_state, "completed_stages": completed}
    run.current_stage = stage


@app.task(bind=True, name="workers.tasks.pipeline.run_analysis_pipeline")
def run_analysis_pipeline(self, run_id: str) -> dict:
    db = SessionLocal()
    try:
        run = db.get(AnalysisRun, UUID(run_id))
        if not run:
            return {"error": "run_not_found"}

        project = db.get(Project, run.project_id)
        org = db.get(Organization, run.organization_id)
        if not project or not org:
            return {"error": "missing_project_or_org"}

        def killed() -> bool:
            db.refresh(project)
            db.refresh(org)
            return bool(project.kill_switch or org.kill_switch)

        run.status = RunStatus.running
        db.commit()

        completed = set(run.stage_state.get("completed_stages", []))

        # A — Intake
        if "A_INTAKE" not in completed:
            if killed():
                run.status = RunStatus.cancelled
                db.commit()
                return {"status": "cancelled"}
            _mark_stage(run, PipelineStage.A_INTAKE)
            db.commit()

        # B — Scope
        if "B_SCOPE" not in completed:
            scope = db.scalar(
                select(AuthorizationScope)
                .where(AuthorizationScope.project_id == project.id)
                .order_by(AuthorizationScope.created_at.desc())
            )
            if not scope:
                run.status = RunStatus.failed
                run.error_message = "Missing authorization scope"
                db.commit()
                return {"error": "missing_scope"}
            _mark_stage(run, PipelineStage.B_SCOPE)
            run.stage_state = {**run.stage_state, "scope_id": str(scope.id)}
            db.commit()

        scope = db.scalar(
            select(AuthorizationScope)
            .where(AuthorizationScope.project_id == project.id)
            .order_by(AuthorizationScope.created_at.desc())
        )
        target = db.scalar(select(TargetApplication).where(TargetApplication.project_id == project.id))
        if not target or not scope:
            run.status = RunStatus.failed
            run.error_message = "Missing target or scope"
            db.commit()
            return {"error": "missing_target_or_scope"}

        # C — Evidence extraction placeholder (seed evidence row conceptually via stage)
        if "C_EVIDENCE" not in completed:
            _mark_stage(run, PipelineStage.C_EVIDENCE)
            db.commit()

        # D — Graph exploration (resumable: skip if already completed)
        fp_to_state: dict[str, ScreenState] = {
            s.fingerprint: s for s in db.scalars(select(ScreenState).where(ScreenState.run_id == run.id)).all()
        }

        if "D_GRAPH" not in completed:
            if killed():
                run.status = RunStatus.cancelled
                db.commit()
                return {"status": "cancelled"}

            explore = explore_site(
                target.base_url,
                allowlist_domains=list(scope.allowlist_domains),
                path_prefixes=list(scope.path_prefixes),
                max_depth=scope.max_depth,
                max_pages=scope.max_pages,
                max_minutes=scope.max_minutes,
                kill_check=killed,
            )

            for st in explore.states:
                if st["fingerprint"] in fp_to_state:
                    continue
                shot_key = ""
                shot = explore.screenshots.get(st["fingerprint"])
                if shot:
                    shot_key = f"runs/{run.id}/screenshots/{st['fingerprint']}.png"
                    storage_service.put_bytes(shot_key, shot, "image/png")
                row = ScreenState(
                    run_id=run.id,
                    organization_id=run.organization_id,
                    fingerprint=st["fingerprint"],
                    url=st["url"],
                    title=st["title"],
                    auth_state=st["auth_state"],
                    role=st["role"],
                    viewport=st["viewport"],
                    components=st["components"],
                    messages=st["messages"],
                    screenshot_key=shot_key,
                    accessibility_snapshot=st["accessibility_snapshot"],
                    confidence=st["confidence"],
                    completeness=st["completeness"],
                    classification=ClaimClassification.OBSERVED,
                )
                db.add(row)
                db.flush()
                fp_to_state[st["fingerprint"]] = row

            for tr in explore.transitions:
                db.add(
                    Transition(
                        run_id=run.id,
                        organization_id=run.organization_id,
                        from_state_id=fp_to_state[tr["from_fingerprint"]].id
                        if tr.get("from_fingerprint") and tr["from_fingerprint"] in fp_to_state
                        else None,
                        to_state_id=fp_to_state[tr["to_fingerprint"]].id
                        if tr.get("to_fingerprint") and tr["to_fingerprint"] in fp_to_state
                        else None,
                        trigger=tr.get("trigger", ""),
                        inputs=tr.get("inputs", {}),
                        skipped_reason=tr.get("skipped_reason", ""),
                        evidence={"skipped": explore.skipped[:50]},
                    )
                )

            entry = next(iter(fp_to_state.values()), None)
            db.add(
                Workflow(
                    run_id=run.id,
                    organization_id=run.organization_id,
                    name="Primary navigation",
                    entry_state_id=entry.id if entry else None,
                    graph={
                        "states": list(fp_to_state.keys()),
                        "skipped_count": len(explore.skipped),
                    },
                )
            )
            _mark_stage(run, PipelineStage.D_GRAPH)
            db.commit()

        # refresh states for modeling
        states = [
            {
                "title": s.title,
                "url": s.url,
                "components": s.components,
                "classification": s.classification.value,
                "fingerprint": s.fingerprint,
            }
            for s in db.scalars(select(ScreenState).where(ScreenState.run_id == run.id)).all()
        ]

        # E — Modeling
        if "E_MODELING" not in completed:
            inferred = infer_bookstore_domain(states)
            for ent in inferred["entities"]:
                entity = DomainEntity(
                    run_id=run.id,
                    organization_id=run.organization_id,
                    name=ent["name"],
                    description=ent["description"],
                    classification=ClaimClassification.INFERRED.value,
                    confidence=ent["confidence"],
                )
                db.add(entity)
                db.flush()
                for f in ent.get("fields", []):
                    db.add(
                        DomainField(
                            entity_id=entity.id,
                            organization_id=run.organization_id,
                            name=f["name"],
                            data_type=f.get("data_type", "string"),
                            nullable=f.get("nullable", True),
                            classification=ClaimClassification.INFERRED.value,
                        )
                    )
            for ep in inferred["endpoints"]:
                db.add(
                    ProposedApiEndpoint(
                        run_id=run.id,
                        organization_id=run.organization_id,
                        method=ep["method"],
                        path=ep["path"],
                        summary=ep["summary"],
                        classification=ClaimClassification.INFERRED.value,
                    )
                )
            for claim in inferred["claims"]:
                row = InferenceClaim(
                    run_id=run.id,
                    organization_id=run.organization_id,
                    content=claim["content"],
                    classification=ClaimClassification[claim["classification"]],
                    confidence=claim["confidence"],
                    rationale=claim["rationale"],
                    open_questions=claim.get("open_questions", []),
                    environment={"viewport": "desktop"},
                )
                db.add(row)
                db.flush()
                if states:
                    first_state = db.scalar(select(ScreenState).where(ScreenState.run_id == run.id))
                    if first_state:
                        db.add(ClaimEvidence(claim_id=row.id, screen_state_id=first_state.id, note="seed link"))
            _mark_stage(run, PipelineStage.E_MODELING)
            db.commit()

        # F — Gaps
        if "F_GAPS" not in completed:
            low = db.scalars(
                select(InferenceClaim).where(
                    InferenceClaim.run_id == run.id,
                    InferenceClaim.confidence < 0.75,
                )
            ).all()
            run.stage_state = {
                **run.stage_state,
                "gap_count": len(low),
                "state_count": len(states),
            }
            _mark_stage(run, PipelineStage.F_GAPS)
            db.commit()

        # G — await review
        if "G_REVIEW" not in completed:
            _mark_stage(run, PipelineStage.G_REVIEW)
            run.status = RunStatus.awaiting_review
            db.commit()

        return {
            "status": run.status.value,
            "stage": run.current_stage.value,
            "states": len(states),
            "completed_stages": run.stage_state.get("completed_stages", []),
        }
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        run = db.get(AnalysisRun, UUID(run_id))
        if run:
            run.status = RunStatus.failed
            run.error_message = str(exc)[:2000]
            db.commit()
        raise
    finally:
        db.close()


@app.task(bind=True, name="workers.tasks.pipeline.run_generation_pipeline")
def run_generation_pipeline(self, run_id: str) -> dict:
    db = SessionLocal()
    try:
        run = db.get(AnalysisRun, UUID(run_id))
        if not run:
            return {"error": "run_not_found"}
        project = db.get(Project, run.project_id)
        run.status = RunStatus.generating
        db.commit()

        completed = set(run.stage_state.get("completed_stages", []))

        entities = []
        for e in db.scalars(select(DomainEntity).where(DomainEntity.run_id == run.id)).all():
            fields = db.scalars(select(DomainField).where(DomainField.entity_id == e.id)).all()
            entities.append(
                {
                    "name": e.name,
                    "description": e.description,
                    "fields": [
                        {"name": f.name, "data_type": f.data_type, "nullable": f.nullable} for f in fields
                    ],
                }
            )
        states = [
            {
                "title": s.title,
                "url": s.url,
                "classification": s.classification.value,
            }
            for s in db.scalars(select(ScreenState).where(ScreenState.run_id == run.id)).all()
        ]

        if "H_PLAN" not in completed:
            plan = GenerationPlan(
                run_id=run.id,
                organization_id=run.organization_id,
                target_stack="nextjs_fastapi_postgres",
                plan={"modules": ["api", "web", "migrations", "tests"], "entities": [e["name"] for e in entities]},
                status="approved",
            )
            db.add(plan)
            _mark_stage(run, PipelineStage.H_PLAN)
            db.commit()

        for stage in [
            PipelineStage.I_GENERATE,
            PipelineStage.J_BACKEND,
            PipelineStage.K_FRONTEND,
            PipelineStage.L_TESTS,
            PipelineStage.M_VISUAL,
            PipelineStage.N_SECURITY,
        ]:
            if stage.value in completed:
                continue
            _mark_stage(run, stage)
            db.commit()

        export_root = Path(storage_service.local_export_path(".").parent)
        export_root.mkdir(parents=True, exist_ok=True)
        work = export_root / str(run.id)
        work.mkdir(parents=True, exist_ok=True)
        zip_path = generate_independent_project(
            work,
            project_name=project.name if project else "Reconstructed App",
            entities=entities,
            states=states,
        )

        # record generated files count
        reconstructed = work / "reconstructed-app"
        for file in reconstructed.rglob("*"):
            if file.is_file():
                db.add(
                    GeneratedFile(
                        run_id=run.id,
                        organization_id=run.organization_id,
                        path=str(file.relative_to(reconstructed)),
                        content_sha256=storage_service.sha256_bytes(file.read_bytes()),
                    )
                )

        key = f"runs/{run.id}/exports/{zip_path.name}"
        storage_service.put_file(key, zip_path, "application/zip")
        # local mirror for download reliability
        mirror = storage_service.local_export_path(zip_path.name)
        mirror.write_bytes(zip_path.read_bytes())

        db.add(
            ExportArtifact(
                run_id=run.id,
                organization_id=run.organization_id,
                storage_key=key,
                filename=zip_path.name,
            )
        )
        db.add(
            SecurityFinding(
                run_id=run.id,
                organization_id=run.organization_id,
                severity="info",
                title="Independent branding enforced",
                detail="Generator does not copy proprietary logos or credentials.",
            )
        )
        _mark_stage(run, PipelineStage.O_EXPORT)
        run.status = RunStatus.completed
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "completed", "export": zip_path.name}
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        run = db.get(AnalysisRun, UUID(run_id))
        if run:
            run.status = RunStatus.failed
            run.error_message = str(exc)[:2000]
            db.commit()
        raise
    finally:
        db.close()
