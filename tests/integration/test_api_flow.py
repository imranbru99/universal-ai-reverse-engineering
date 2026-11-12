"""Live-stack integration checks. Run: pytest tests/integration/test_api_flow.py -q"""

from __future__ import annotations

import os
import time
import uuid

import httpx
import pytest

API = os.getenv("API_PUBLIC_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=API, timeout=60.0) as c:
        # wait for API
        for _ in range(60):
            try:
                r = c.get("/api/v1/health")
                if r.status_code == 200:
                    yield c
                    return
            except Exception:
                pass
            time.sleep(2)
        pytest.skip("API not reachable")


def _register(client: httpx.Client, prefix: str):
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass!234",
            "full_name": prefix,
            "organization_name": f"Org {prefix}",
        },
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    return tokens["access_token"]


def test_health(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"


def test_cross_tenant_run_hidden(client):
    token_a = _register(client, "alice")
    token_b = _register(client, "bob")

    orgs = client.get("/api/v1/orgs", headers={"Authorization": f"Bearer {token_a}"}).json()
    org_id = orgs[0]["id"]
    created = client.post(
        f"/api/v1/orgs/{org_id}/projects",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "name": "Alice Project",
            "description": "tenant isolation",
            "target_url": "http://demo-target:3100",
            "authorization_declaration": "I am authorized to analyze the bundled demo target non-destructively.",
            "allowlist_domains": ["demo-target", "localhost"],
            "path_prefixes": ["/"],
            "max_depth": 2,
            "max_pages": 5,
            "max_minutes": 3,
        },
    )
    assert created.status_code == 200, created.text
    project_id = created.json()["id"]
    run = client.post(
        f"/api/v1/projects/{project_id}/analysis-runs",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert run.status_code == 200, run.text
    run_id = run.json()["id"]

    denied = client.get(
        f"/api/v1/analysis-runs/{run_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert denied.status_code == 404


def test_private_ip_rejected(client):
    token = _register(client, "ssrf")
    orgs = client.get("/api/v1/orgs", headers={"Authorization": f"Bearer {token}"}).json()
    org_id = orgs[0]["id"]
    resp = client.post(
        f"/api/v1/orgs/{org_id}/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Bad Target",
            "description": "ssrf",
            "target_url": "http://127.0.0.1:22",
            "authorization_declaration": "I am authorized to analyze this target within policy.",
            "allowlist_domains": ["127.0.0.1"],
            "path_prefixes": ["/"],
        },
    )
    assert resp.status_code == 400
