from __future__ import annotations

from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_project_for_user, require_org_role
from app.db import get_db
from app.models import AuthorizationScope, Organization, Project, TargetApplication, TargetVersion, User
from app.models.entities import RoleEnum
from app.schemas.api import ProjectCreate, ProjectOut, ScopeOut
from app.security.url_guard import UrlGuardError, validate_public_http_url
from app.services.audit import audit

router = APIRouter()


@router.post("/orgs/{org_id}/projects", response_model=ProjectOut)
def create_project(
    org_id: UUID,
    body: ProjectCreate,
    ctx=Depends(require_org_role(RoleEnum.analyst)),
    db: Session = Depends(get_db),
):
    user, org, _membership = ctx
    if org.kill_switch:
        raise HTTPException(status_code=403, detail="Organization kill switch active")

    try:
        validate_public_http_url(body.target_url, allow_trusted_internal=True)
    except UrlGuardError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    host = urlparse(body.target_url).hostname or ""
    domains = [d.lower() for d in body.allowlist_domains]
    if host.lower() not in domains and not any(host.lower().endswith("." + d) for d in domains):
        # Auto-include target host if missing to reduce footguns, but still require declaration
        domains.append(host.lower())

    project = Project(
        organization_id=org.id,
        name=body.name,
        description=body.description,
        status="ready",
    )
    db.add(project)
    db.flush()

    target = TargetApplication(
        project_id=project.id,
        organization_id=org.id,
        name=body.target_name,
        base_url=body.target_url.rstrip("/"),
        app_type="web",
    )
    db.add(target)
    db.flush()
    db.add(TargetVersion(target_id=target.id, label="initial"))

    scope = AuthorizationScope(
        project_id=project.id,
        organization_id=org.id,
        declaration_text=body.authorization_declaration,
        allowlist_domains=domains,
        path_prefixes=body.path_prefixes or ["/"],
        max_depth=body.max_depth,
        max_pages=body.max_pages,
        max_minutes=body.max_minutes,
        allow_authenticated=body.allow_authenticated,
        signed_by_user_id=user.id,
    )
    db.add(scope)
    audit(
        db,
        action="project.create",
        organization_id=org.id,
        actor_user_id=user.id,
        resource_type="project",
        resource_id=str(project.id),
        detail={"target_url": body.target_url, "domains": domains},
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: UUID, ctx=Depends(get_project_for_user)):
    _user, project, _membership = ctx
    return project


@router.get("/projects/{project_id}/scope", response_model=ScopeOut)
def get_scope(project_id: UUID, ctx=Depends(get_project_for_user), db: Session = Depends(get_db)):
    _user, project, _membership = ctx
    scope = db.scalar(
        select(AuthorizationScope)
        .where(AuthorizationScope.project_id == project.id)
        .order_by(AuthorizationScope.created_at.desc())
    )
    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")
    return scope


@router.post("/projects/{project_id}/kill-switch", response_model=ProjectOut)
def toggle_kill_switch(
    project_id: UUID,
    enabled: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # require admin+
    from app.api.deps import ROLE_RANK

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    from app.models import Membership

    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == project.organization_id,
            Membership.user_id == user.id,
        )
    )
    if not membership or ROLE_RANK[membership.role] < ROLE_RANK[RoleEnum.admin]:
        raise HTTPException(status_code=404, detail="Project not found")
    project.kill_switch = enabled
    audit(
        db,
        action="project.kill_switch",
        organization_id=project.organization_id,
        actor_user_id=user.id,
        resource_type="project",
        resource_id=str(project.id),
        detail={"enabled": enabled},
    )
    db.commit()
    db.refresh(project)
    return project
