from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.config import get_settings


class BasicRateLimitMiddleware(BaseHTTPMiddleware):
    """Simple per-IP fixed window limiter for abuse resistance in MVP."""

    def __init__(self, app, limit: int = 120):
        super().__init__(app)
        self.limit = limit
        self.hits: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        import time

        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = self.hits.setdefault(ip, [])
        self.hits[ip] = [t for t in window if now - t < 60]
        if len(self.hits[ip]) >= self.limit:
            return Response("Rate limit exceeded", status_code=429)
        self.hits[ip].append(now)
        return await call_next(request)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(BasicRateLimitMiddleware)
    app.include_router(api_router)

    @app.get("/")
    def root():
        return {"name": settings.app_name, "docs": "/docs"}

    return app


app = create_app()
