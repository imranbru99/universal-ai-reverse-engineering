"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { createProject, listOrgs } from "@/lib/api";

export default function NewProjectPage() {
  const [orgId, setOrgId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    target_url: "http://demo-target:3100",
    authorization_declaration:
      "I am authorized to analyze this target non-destructively within the declared domain allowlist and budgets.",
    allowlist_domains: "demo-target,localhost",
    path_prefixes: "/",
    max_depth: 4,
    max_pages: 30,
    max_minutes: 8,
  });

  useEffect(() => {
    const token = localStorage.getItem("rf_access");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    listOrgs(token).then((orgs) => {
      if (orgs[0]) setOrgId(orgs[0].id);
    });
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const token = localStorage.getItem("rf_access");
    if (!token || !orgId) return;
    setLoading(true);
    setError("");
    try {
      await createProject(token, orgId, {
        name: form.name,
        description: form.description,
        target_url: form.target_url,
        authorization_declaration: form.authorization_declaration,
        allowlist_domains: form.allowlist_domains.split(",").map((s) => s.trim()).filter(Boolean),
        path_prefixes: form.path_prefixes.split(",").map((s) => s.trim()).filter(Boolean),
        max_depth: Number(form.max_depth),
        max_pages: Number(form.max_pages),
        max_minutes: Number(form.max_minutes),
        allow_authenticated: false,
      });
      window.location.href = "/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-2xl px-6 py-10">
      <Link href="/dashboard" className="text-sm text-accent-700">
        ← Dashboard
      </Link>
      <h1 className="mt-4 font-display text-3xl">New project wizard</h1>
      <p className="mt-2 text-sm text-ink-500">Authorization declaration is required before exploration.</p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        {(
          [
            ["name", "Project name"],
            ["description", "Description"],
            ["target_url", "Target URL"],
            ["allowlist_domains", "Allowlist domains (comma-separated)"],
            ["path_prefixes", "Path prefixes (comma-separated)"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className="block text-sm">
            {label}
            <input
              className="mt-1 w-full border border-ink-700/20 bg-white/80 px-3 py-2"
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              required={key === "name" || key === "target_url"}
            />
          </label>
        ))}
        <label className="block text-sm">
          Authorization declaration
          <textarea
            className="mt-1 w-full border border-ink-700/20 bg-white/80 px-3 py-2"
            rows={4}
            value={form.authorization_declaration}
            onChange={(e) => setForm({ ...form, authorization_declaration: e.target.value })}
            required
            minLength={20}
          />
        </label>
        <div className="grid grid-cols-3 gap-3">
          {(["max_depth", "max_pages", "max_minutes"] as const).map((key) => (
            <label key={key} className="block text-sm">
              {key}
              <input
                type="number"
                className="mt-1 w-full border border-ink-700/20 bg-white/80 px-3 py-2"
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: Number(e.target.value) })}
              />
            </label>
          ))}
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button disabled={loading} className="bg-accent-700 px-4 py-2 text-white disabled:opacity-60">
          {loading ? "Creating…" : "Create project"}
        </button>
      </form>
    </main>
  );
}
