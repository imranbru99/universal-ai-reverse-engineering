from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Membership, Organization, Project, User
from app.models.entities import RoleEnum
from app.security.tokens import safe_decode

bearer = HTTPBearer(auto_error=False)

ROLE_RANK = {
    RoleEnum.viewer: 1,
    RoleEnum.analyst: 2,
    RoleEnum.admin: 3,
    RoleEnum.owner: 4,
}


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = safe_decode(creds.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing")
    return user


def require_org_role(min_role: RoleEnum):
    def _dep(
        org_id: UUID,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> tuple[User, Organization, Membership]:
        org = db.get(Organization, org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        membership = db.scalar(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.user_id == user.id,
            )
        )
        if not membership or ROLE_RANK[membership.role] < ROLE_RANK[min_role]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user, org, membership

    return _dep


def get_project_for_user(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    min_role: RoleEnum = RoleEnum.viewer,
) -> tuple[User, Project, Membership]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == project.organization_id,
            Membership.user_id == user.id,
        )
    )
    if not membership or ROLE_RANK[membership.role] < ROLE_RANK[min_role]:
        # Hide existence across tenants
        raise HTTPException(status_code=404, detail="Project not found")
    return user, project, membership
