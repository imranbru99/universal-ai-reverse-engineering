"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { register } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    organization_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = await register(form);
      localStorage.setItem("rf_access", tokens.access_token);
      localStorage.setItem("rf_refresh", tokens.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <Link href="/" className="mb-8 font-display text-2xl">
        REVERSEFORGE AI
      </Link>
      <h1 className="text-2xl font-medium">Create account</h1>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        {(["full_name", "organization_name", "email", "password"] as const).map((key) => (
          <label key={key} className="block text-sm capitalize">
            {key.replace("_", " ")}
            <input
              className="mt-1 w-full border border-ink-700/20 bg-white/80 px-3 py-2"
              type={key === "password" ? "password" : key === "email" ? "email" : "text"}
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              required
              minLength={key === "password" ? 8 : undefined}
            />
          </label>
        ))}
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button disabled={loading} className="w-full bg-accent-700 px-4 py-2 text-white disabled:opacity-60">
          {loading ? "Creating…" : "Create account"}
        </button>
      </form>
    </main>
  );
}
