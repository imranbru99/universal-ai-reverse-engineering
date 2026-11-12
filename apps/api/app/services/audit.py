from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditEvent


def audit(
    db: Session,
    *,
    action: str,
    organization_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    resource_type: str = "",
    resource_id: str = "",
    detail: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail or {},
        )
    )
