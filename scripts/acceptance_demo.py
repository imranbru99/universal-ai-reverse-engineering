#!/usr/bin/env python3
"""Acceptance path against a live Compose stack."""

from __future__ import annotations

import sys
import time

import httpx

API = "http://localhost:8000"


def main() -> int:
    client = httpx.Client(base_url=API, timeout=60.0)
    for _ in range(30):
        try:
            if client.get("/api/v1/health").status_code == 200:
                break
        except Exception:
            time.sleep(2)
    else:
        print("API not ready")
        return 1

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "DemoOwner!234"},
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.get("/api/v1/orgs", headers=headers).json()[0]["id"]
    project_id = client.get(f"/api/v1/orgs/{org_id}/projects", headers=headers).json()[0]["id"]
    print("project", project_id)

    run = client.post(f"/api/v1/projects/{project_id}/analysis-runs", headers=headers)
    run.raise_for_status()
    run_id = run.json()["id"]
    print("run", run_id)

    status = ""
    for i in range(90):
        r = client.get(f"/api/v1/analysis-runs/{run_id}", headers=headers).json()
        status = r["status"]
        print(f"[{i}] {status} {r['current_stage']} {r.get('error_message','')}")
        if status in {"awaiting_review", "completed", "failed", "cancelled"}:
            break
        time.sleep(2)
    if status == "failed":
        return 2
    if status not in {"awaiting_review", "completed"}:
        print("timeout waiting for analysis")
        return 3

    states = client.get(f"/api/v1/analysis-runs/{run_id}/states", headers=headers).json()
    transitions = client.get(f"/api/v1/analysis-runs/{run_id}/transitions", headers=headers).json()
    claims = client.get(f"/api/v1/analysis-runs/{run_id}/claims", headers=headers).json()
    entities = client.get(f"/api/v1/analysis-runs/{run_id}/entities", headers=headers).json()
    print(
        f"states={len(states)} transitions={len(transitions)} claims={len(claims)} entities={len(entities)}"
    )
    if not states:
        print("no states observed")
        return 4

    if claims:
        client.post(
            f"/api/v1/claims/{claims[0]['id']}/review",
            headers=headers,
            json={"decision": "approve"},
        ).raise_for_status()

    gen = client.post(f"/api/v1/analysis-runs/{run_id}/generate", headers=headers)
    gen.raise_for_status()
    for i in range(60):
        r = client.get(f"/api/v1/analysis-runs/{run_id}", headers=headers).json()
        print(f"[g{i}] {r['status']} {r['current_stage']} {r.get('error_message','')}")
        if r["status"] in {"completed", "failed"}:
            status = r["status"]
            break
        time.sleep(2)
    if status != "completed":
        return 5

    export = client.get(f"/api/v1/analysis-runs/{run_id}/export", headers=headers)
    export.raise_for_status()
    print("export", export.json()["filename"])

    # tenant isolation smoke
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other{int(time.time())}@example.com",
            "password": "OtherPass!234",
            "full_name": "Other",
            "organization_name": "Other Org",
        },
    )
    other.raise_for_status()
    other_token = other.json()["access_token"]
    denied = client.get(
        f"/api/v1/analysis-runs/{run_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    print("cross_tenant", denied.status_code)
    if denied.status_code != 404:
        return 6

    print("ACCEPTANCE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
