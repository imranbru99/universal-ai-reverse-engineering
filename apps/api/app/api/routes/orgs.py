from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_org_role
from app.db import get_db
from app.models import Membership, Organization, Project, User
from app.models.entities import RoleEnum
from app.schemas.api import OrgOut, ProjectOut

router = APIRouter()


@router.get("", response_model=list[OrgOut])
def list_orgs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == user.id)
        .order_by(Organization.created_at.desc())
    ).all()
    return rows


@router.get("/{org_id}/projects", response_model=list[ProjectOut])
def list_projects(
    org_id: UUID,
    ctx=Depends(require_org_role(RoleEnum.viewer)),
    db: Session = Depends(get_db),
):
    _user, _org, _membership = ctx
    return db.scalars(
        select(Project).where(Project.organization_id == org_id).order_by(Project.created_at.desc())
    ).all()
