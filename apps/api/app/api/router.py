from fastapi import APIRouter

from app.api.routes import analysis, auth, health, orgs, projects

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(orgs.router, prefix="/orgs", tags=["organizations"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(analysis.router, tags=["analysis"])
