"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-lg py-16 text-center">
      <h1 className="text-xl font-bold text-[var(--foreground)]">
        Something went wrong
      </h1>
      <p className="mt-2 text-sm text-[var(--muted)]">{error.message}</p>
      <button
        type="button"
        onClick={reset}
        className="mt-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-medium text-[var(--foreground)] transition hover:bg-[var(--surface)]/80"
      >
        Try again
      </button>
    </div>
  );
}
