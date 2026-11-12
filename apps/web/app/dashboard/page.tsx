"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listOrgs, listProjects, me, startAnalysis } from "@/lib/api";

type Project = { id: string; name: string; description: string; status: string; organization_id: string };

export default function DashboardPage() {
  const [user, setUser] = useState<{ email: string; full_name: string } | null>(null);
  const [orgId, setOrgId] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("rf_access");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    (async () => {
      try {
        const u = await me(token);
        setUser(u);
        const orgs = await listOrgs(token);
        if (!orgs.length) return;
        setOrgId(orgs[0].id);
        const projs = await listProjects(token, orgs[0].id);
        setProjects(projs);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      }
    })();
  }, []);

  async function analyze(projectId: string) {
    const token = localStorage.getItem("rf_access");
    if (!token) return;
    setBusy(projectId);
    setError("");
    try {
      const run = await startAnalysis(token, projectId);
      window.location.href = `/runs/${run.id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis");
      setBusy(null);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <header className="mb-10 flex items-end justify-between gap-4">
        <div>
          <p className="font-display text-2xl">REVERSEFORGE AI</p>
          <p className="text-sm text-ink-500">{user ? `${user.full_name} · ${user.email}` : "Loading…"}</p>
        </div>
        <Link href="/projects/new" className="bg-accent-700 px-4 py-2 text-sm text-white">
          New project
        </Link>
      </header>

      {error ? <p className="mb-4 text-sm text-red-700">{error}</p> : null}

      <section>
        <h1 className="mb-4 text-xl font-medium">Projects</h1>
        <div className="space-y-3">
          {projects.map((p) => (
            <article key={p.id} className="panel flex flex-wrap items-center justify-between gap-3 p-4">
              <div>
                <h2 className="font-medium">{p.name}</h2>
                <p className="text-sm text-ink-500">{p.description || "No description"}</p>
              </div>
              <button
                onClick={() => analyze(p.id)}
                disabled={busy === p.id}
                className="border border-ink-700/20 px-3 py-2 text-sm disabled:opacity-50"
              >
                {busy === p.id ? "Starting…" : "Start analysis"}
              </button>
            </article>
          ))}
          {!projects.length ? <p className="text-sm text-ink-500">No projects yet. Create one to begin.</p> : null}
        </div>
        {orgId ? <p className="mt-6 text-xs text-ink-500">Org: {orgId}</p> : null}
      </section>
    </main>
  );
}
