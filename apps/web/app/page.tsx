import Link from "next/link";

export default function HomePage() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2280%22 height=%2280%22 viewBox=%220 0 80 80%22%3E%3Cg fill=%22%23221f1b%22 fill-opacity=%220.03%22%3E%3Cpath d=%22M0 0h40v40H0zM40 40h40v40H40z%22/%3E%3C/g%3E%3C/svg%3E')]" />
      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col justify-between px-6 py-10">
        <header className="flex items-center justify-between">
          <p className="font-display text-xl tracking-tight">REVERSEFORGE AI</p>
          <Link href="/login" className="text-sm text-accent-700 underline-offset-4 hover:underline">
            Sign in
          </Link>
        </header>

        <section className="max-w-3xl py-24">
          <p className="badge mb-6 border-accent-600/30 text-accent-700">Authorized analysis only</p>
          <h1 className="font-display text-5xl leading-[1.05] tracking-tight md:text-6xl">
            Map observable behavior.
            <span className="block text-accent-700">Reconstruct independently.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg text-ink-700 dark:text-paper-200/80">
            Evidence-backed state graphs, provenance-tagged inference, and a first-class generation
            target — without pretending to see private source, schemas, or secrets.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link
              href="/login"
              className="bg-accent-700 px-5 py-3 text-sm font-medium text-white transition hover:bg-accent-600"
            >
              Open workspace
            </Link>
            <Link href="/register" className="border border-ink-700/20 px-5 py-3 text-sm">
              Create account
            </Link>
          </div>
        </section>

        <footer className="text-sm text-ink-500">OBS / INF / CONF / UNK claim classifications enforced.</footer>
      </div>
    </main>
  );
}
