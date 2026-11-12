const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type TokenPair = { access_token: string; refresh_token: string; token_type: string };

function authHeaders(token?: string | null): HeadersInit {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  return parse<TokenPair>(
    await fetch(`${API_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ email, password }),
    })
  );
}

export async function register(payload: {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
}) {
  return parse<TokenPair>(
    await fetch(`${API_URL}/api/v1/auth/register`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    })
  );
}

export async function me(token: string) {
  return parse<{ id: string; email: string; full_name: string }>(
    await fetch(`${API_URL}/api/v1/auth/me`, { headers: authHeaders(token) })
  );
}

export async function listOrgs(token: string) {
  return parse<Array<{ id: string; name: string; slug: string; kill_switch: boolean }>>(
    await fetch(`${API_URL}/api/v1/orgs`, { headers: authHeaders(token) })
  );
}

export async function listProjects(token: string, orgId: string) {
  return parse<
    Array<{ id: string; name: string; description: string; status: string; organization_id: string }>
  >(await fetch(`${API_URL}/api/v1/orgs/${orgId}/projects`, { headers: authHeaders(token) }));
}

export async function createProject(token: string, orgId: string, body: Record<string, unknown>) {
  return parse<{ id: string; name: string }>(
    await fetch(`${API_URL}/api/v1/orgs/${orgId}/projects`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify(body),
    })
  );
}

export async function startAnalysis(token: string, projectId: string) {
  return parse<{ id: string; status: string; current_stage: string }>(
    await fetch(`${API_URL}/api/v1/projects/${projectId}/analysis-runs`, {
      method: "POST",
      headers: authHeaders(token),
    })
  );
}

export async function getRun(token: string, runId: string) {
  return parse<{
    id: string;
    status: string;
    current_stage: string;
    stage_state: Record<string, unknown>;
    error_message: string;
  }>(await fetch(`${API_URL}/api/v1/analysis-runs/${runId}`, { headers: authHeaders(token) }));
}

export async function getStates(token: string, runId: string) {
  return parse<
    Array<{
      id: string;
      url: string;
      title: string;
      confidence: number;
      classification: string;
      components: unknown[];
    }>
  >(await fetch(`${API_URL}/api/v1/analysis-runs/${runId}/states`, { headers: authHeaders(token) }));
}

export async function getTransitions(token: string, runId: string) {
  return parse<
    Array<{ id: string; trigger: string; from_state_id: string | null; to_state_id: string | null; skipped_reason: string }>
  >(await fetch(`${API_URL}/api/v1/analysis-runs/${runId}/transitions`, { headers: authHeaders(token) }));
}

export async function getClaims(token: string, runId: string) {
  return parse<
    Array<{
      id: string;
      content: string;
      classification: string;
      confidence: number;
      rationale: string;
      review_status: string;
    }>
  >(await fetch(`${API_URL}/api/v1/analysis-runs/${runId}/claims`, { headers: authHeaders(token) }));
}

export async function getEntities(token: string, runId: string) {
  return parse<
    Array<{ id: string; name: string; description: string; classification: string; confidence: number; fields: unknown[] }>
  >(await fetch(`${API_URL}/api/v1/analysis-runs/${runId}/entities`, { headers: authHeaders(token) }));
}

export async function reviewClaim(token: string, claimId: string, decision: string, correction_text = "") {
  return parse(
    await fetch(`${API_URL}/api/v1/claims/${claimId}/review`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ decision, correction_text }),
    })
  );
}

export async function generate(token: string, runId: string) {
  return parse(await fetch(`${API_URL}/api/v1/analysis-runs/${runId}/generate`, { method: "POST", headers: authHeaders(token) }));
}

export async function getExport(token: string, runId: string) {
  return parse<{ id: string; filename: string; download_url: string }>(
    await fetch(`${API_URL}/api/v1/analysis-runs/${runId}/export`, { headers: authHeaders(token) })
  );
}

export { API_URL };
