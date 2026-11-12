"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  API_URL,
  generate,
  getClaims,
  getEntities,
  getExport,
  getRun,
  getStates,
  getTransitions,
  reviewClaim,
} from "@/lib/api";

export default function RunWorkspacePage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;
  const [run, setRun] = useState<any>(null);
  const [states, setStates] = useState<any[]>([]);
  const [transitions, setTransitions] = useState<any[]>([]);
  const [claims, setClaims] = useState<any[]>([]);
  const [entities, setEntities] = useState<any[]>([]);
  const [exportInfo, setExportInfo] = useState<any>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    const token = localStorage.getItem("rf_access");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    try {
      const [r, s, t, c, e] = await Promise.all([
        getRun(token, runId),
        getStates(token, runId),
        getTransitions(token, runId),
        getClaims(token, runId),
        getEntities(token, runId),
      ]);
      setRun(r);
      setStates(s);
      setTransitions(t);
      setClaims(c);
      setEntities(e);
      if (r.status === "completed") {
        try {
          setExportInfo(await getExport(token, runId));
        } catch {
          setExportInfo(null);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run");
    }
  }, [runId]);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [refresh]);

  async function onReview(claimId: string, decision: string) {
    const token = localStorage.getItem("rf_access");
    if (!token) return;
    await reviewClaim(token, claimId, decision);
    await refresh();
  }

  async function onGenerate() {
    const token = localStorage.getItem("rf_access");
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      await generate(token, runId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link href="/dashboard" className="text-sm text-accent-700">
            ← Dashboard
          </Link>
          <h1 className="mt-2 font-display text-3xl">Analysis workspace</h1>
          <p className="text-sm text-ink-500">
            Run {runId} · {run?.status || "…"} · stage {run?.current_stage || "…"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onGenerate}
            disabled={busy}
            className="bg-accent-700 px-4 py-2 text-sm text-white disabled:opacity-60"
          >
            {busy ? "Generating…" : "Generate reconstruction"}
          </button>
          {exportInfo ? (
            <a
              className="border border-ink-700/20 px-4 py-2 text-sm"
              href={`${API_URL}/api/v1/exports/${exportInfo.id}/download`}
              onClick={(e) => {
                e.preventDefault();
                const token = localStorage.getItem("rf_access");
                fetch(`${API_URL}/api/v1/exports/${exportInfo.id}/download`, {
                  headers: { Authorization: `Bearer ${token}` },
                })
                  .then((r) => r.blob())
                  .then((blob) => {
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = exportInfo.filename;
                    a.click();
                  });
              }}
            >
              Download ZIP
            </a>
          ) : null}
        </div>
      </div>

      {error ? <p className="mb-4 text-sm text-red-700">{error}</p> : null}
      {run?.error_message ? <p className="mb-4 text-sm text-red-700">{run.error_message}</p> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="panel p-4">
          <h2 className="mb-3 font-medium">Screen states ({states.length})</h2>
          <ul className="max-h-80 space-y-2 overflow-auto text-sm">
            {states.map((s) => (
              <li key={s.id} className="border-b border-ink-700/10 pb-2">
                <div className="flex items-center justify-between gap-2">
                  <strong>{s.title || s.url}</strong>
                  <span className="badge">{s.classification}</span>
                </div>
                <p className="text-ink-500">{s.url}</p>
                <p className="text-xs">confidence {s.confidence} · components {s.components?.length || 0}</p>
              </li>
            ))}
            {!states.length ? <li className="text-ink-500">Waiting for exploration…</li> : null}
          </ul>
        </section>

        <section className="panel p-4">
          <h2 className="mb-3 font-medium">Transitions ({transitions.length})</h2>
          <ul className="max-h-80 space-y-2 overflow-auto text-sm">
            {transitions.map((t) => (
              <li key={t.id} className="border-b border-ink-700/10 pb-2">
                <code className="text-xs">{t.trigger}</code>
                {t.skipped_reason ? (
                  <p className="text-amber-800">skipped: {t.skipped_reason}</p>
                ) : (
                  <p className="text-ink-500">
                    {t.from_state_id?.slice(0, 8)} → {t.to_state_id?.slice(0, 8)}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>

        <section className="panel p-4">
          <h2 className="mb-3 font-medium">Inference claims</h2>
          <ul className="space-y-3 text-sm">
            {claims.map((c) => (
              <li key={c.id} className="border border-ink-700/10 p-3">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <span className="badge">{c.classification}</span>
                  <span className="text-xs text-ink-500">conf {c.confidence}</span>
                  <span className="text-xs">review: {c.review_status}</span>
                </div>
                <p>{c.content}</p>
                <p className="mt-1 text-xs text-ink-500">{c.rationale}</p>
                {c.review_status === "pending" ? (
                  <div className="mt-2 flex gap-2">
                    <button className="border px-2 py-1 text-xs" onClick={() => onReview(c.id, "approve")}>
                      Approve
                    </button>
                    <button className="border px-2 py-1 text-xs" onClick={() => onReview(c.id, "reject")}>
                      Reject
                    </button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        </section>

        <section className="panel p-4">
          <h2 className="mb-3 font-medium">Proposed domain model</h2>
          <ul className="space-y-3 text-sm">
            {entities.map((e) => (
              <li key={e.id}>
                <div className="flex items-center gap-2">
                  <strong>{e.name}</strong>
                  <span className="badge">{e.classification}</span>
                </div>
                <p className="text-ink-500">{e.description}</p>
                <ul className="mt-1 list-disc pl-5 text-xs">
                  {(e.fields || []).map((f: any) => (
                    <li key={f.id || f.name}>
                      {f.name}: {f.data_type} ({f.classification})
                    </li>
                  ))}
                </ul>
              </li>
            ))}
            {!entities.length ? <li className="text-ink-500">Entities appear after modeling stage.</li> : null}
          </ul>
        </section>
      </div>
    </main>
  );
}
