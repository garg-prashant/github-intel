import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-[var(--border)] bg-[var(--surface)]">
      <div className="mx-auto max-w-5xl px-6 py-8 sm:px-8 lg:px-10">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <p className="text-sm text-[var(--muted)]">
            Discover trending GitHub repos with AI-generated learning content
          </p>
          <div className="flex items-center gap-6 text-sm">
            <a
              href={`${API_BASE}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--muted)] transition hover:text-[var(--foreground)]"
            >
              API Docs
            </a>
            <Link
              href="/"
              className="text-[var(--muted)] transition hover:text-[var(--foreground)]"
            >
              Trending
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
