"""Provision demo organization, user, and Bookstore project."""

from __future__ import annotations

from urllib.parse import urlparse

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import (
    AuthorizationScope,
    Membership,
    Organization,
    Project,
    TargetApplication,
    TargetVersion,
    User,
)
from app.models.entities import RoleEnum
from app.security.passwords import hash_password


DEMO_EMAIL = "owner@example.com"
DEMO_PASSWORD = "DemoOwner!234"


def seed() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        # Migrate legacy reserved-TLD demo email if present
        legacy_emails = [
            "owner@demo.reverseforge.local",
            "owner@demo.reverseforge.test",
        ]
        user = None
        for legacy_email in legacy_emails:
            legacy = db.scalar(select(User).where(User.email == legacy_email))
            if legacy:
                legacy.email = DEMO_EMAIL
                legacy.password_hash = hash_password(DEMO_PASSWORD)
                user = legacy
                break
        if not user:
            user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
            if not user:
                user = User(
                    email=DEMO_EMAIL,
                    password_hash=hash_password(DEMO_PASSWORD),
                    full_name="Demo Owner",
                )
                db.add(user)
                db.flush()
            else:
                user.password_hash = hash_password(DEMO_PASSWORD)

        org = db.scalar(select(Organization).where(Organization.slug == "demo-org"))
        if not org:
            org = Organization(name="Demo Organization", slug="demo-org")
            db.add(org)
            db.flush()

        membership = db.scalar(
            select(Membership).where(
                Membership.user_id == user.id,
                Membership.organization_id == org.id,
            )
        )
        if not membership:
            db.add(Membership(user_id=user.id, organization_id=org.id, role=RoleEnum.owner))

        project = db.scalar(
            select(Project).where(
                Project.organization_id == org.id,
                Project.name == "Demo Bookstore",
            )
        )
        target_url = settings.demo_target_url.rstrip("/")
        host = urlparse(target_url).hostname or "demo-target"

        if not project:
            project = Project(
                organization_id=org.id,
                name="Demo Bookstore",
                description="Bundled authorized demo application for acceptance tests.",
                status="ready",
            )
            db.add(project)
            db.flush()

            target = TargetApplication(
                project_id=project.id,
                organization_id=org.id,
                name="Demo Bookstore Web",
                base_url=target_url,
                app_type="web",
            )
            db.add(target)
            db.flush()
            db.add(TargetVersion(target_id=target.id, label="demo-v1"))

            db.add(
                AuthorizationScope(
                    project_id=project.id,
                    organization_id=org.id,
                    declaration_text=(
                        "I am authorized to analyze the bundled Demo Bookstore application "
                        "shipped with REVERSEFORGE AI for non-destructive exploration only."
                    ),
                    allowlist_domains=[host, "localhost", "demo-target"],
                    path_prefixes=["/"],
                    max_depth=4,
                    max_pages=30,
                    max_minutes=8,
                    allow_authenticated=True,
                    signed_by_user_id=user.id,
                )
            )

        db.commit()
        print(f"Seeded demo user {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"Demo project target: {target_url}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
