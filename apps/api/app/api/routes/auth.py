from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Membership, Organization, User
from app.models.entities import RoleEnum
from app.schemas.api import LoginRequest, RegisterRequest, TokenPair, UserOut
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, create_refresh_token, safe_decode
from app.services.audit import audit
from app.api.deps import get_current_user

router = APIRouter()


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:80] or "org"


@router.post("/register", response_model=TokenPair)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == body.email.lower()))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name or body.email.split("@")[0],
    )
    db.add(user)
    db.flush()

    base_slug = _slugify(body.organization_name)
    slug = base_slug
    i = 1
    while db.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{base_slug}-{i}"
        i += 1

    org = Organization(name=body.organization_name, slug=slug)
    db.add(org)
    db.flush()
    db.add(Membership(user_id=user.id, organization_id=org.id, role=RoleEnum.owner))
    audit(
        db,
        action="user.register",
        organization_id=org.id,
        actor_user_id=user.id,
        resource_type="organization",
        resource_id=str(org.id),
    )
    db.commit()
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    audit(db, action="user.login", actor_user_id=user.id, resource_type="user", resource_id=str(user.id))
    db.commit()
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(body: dict, db: Session = Depends(get_db)):
    token = body.get("refresh_token", "")
    payload = safe_decode(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    from uuid import UUID

    user = db.get(User, UUID(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
