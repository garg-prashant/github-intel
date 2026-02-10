"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Play, Check, Loader2, Circle, XCircle } from "lucide-react";
import { triggerPipeline, clearExistingData, fetchPipelineStatus, type PipelineStatus } from "@/lib/api";
import { CATEGORY_COLORS } from "@/lib/constants";
import type { CategoryItem } from "@/lib/types";
import { cn } from "@/lib/utils";

const POLL_INTERVAL_MS = 2500;

interface TriggerPipelineButtonProps {
  categories: CategoryItem[];
}

export function TriggerPipelineButton({ categories }: TriggerPipelineButtonProps) {
  const [loading, setLoading] = useState(false);
  const [clearLoading, setClearLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<PipelineStatus | null>(null);
  /** Selected category slugs for scrape; empty = scrape all categories */
  const [scrapeCategories, setScrapeCategories] = useState<Set<string>>(new Set());
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const router = useRouter();

  const toggleScrapeCategory = (slug: string) => {
    setScrapeCategories((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  };

  const selectAllScrapeCategories = () => setScrapeCategories(new Set());

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => () => stopPolling(), [stopPolling]);

  async function handleRun() {
    setLoading(true);
    setMessage(null);
    setError(null);
    setProgress(null);
    stopPolling();
    try {
      const categorySlugs = scrapeCategories.size > 0 ? Array.from(scrapeCategories) : undefined;
      const result = await triggerPipeline(categorySlugs ? { categories: categorySlugs } : undefined);
      if (!result.started || !result.chain_id) {
        setMessage(result.message || "Pipeline did not start.");
        setLoading(false);
        return;
      }
      setMessage("Pipeline started. Tracking progress…");

      const poll = async () => {
        try {
          const status = await fetchPipelineStatus(result.chain_id!);
          setProgress(status);
          if (status.status === "success") {
            stopPolling();
            setLoading(false);
            setMessage("Pipeline finished. Refreshing…");
            router.refresh();
          } else if (status.status === "failure") {
            stopPolling();
            setLoading(false);
            setMessage(null);
            setError(status.error || "Pipeline failed.");
          }
        } catch {
          // keep polling on transient errors
        }
      };

      await poll();
      pollRef.current = setInterval(poll, POLL_INTERVAL_MS);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to trigger pipeline");
      setLoading(false);
    }
  }

  async function handleClear() {
    setClearLoading(true);
    setMessage(null);
    setError(null);
    try {
      const result = await clearExistingData();
      setMessage(result.message);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to clear data");
    } finally {
      setClearLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-3 w-full sm:w-auto">
      {categories.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 w-full sm:justify-end">
          <span className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">Scrape for</span>
          <button
            type="button"
            onClick={selectAllScrapeCategories}
            className={cn(
              "rounded-lg border px-3 py-2 text-sm font-medium transition",
              scrapeCategories.size === 0
                ? "border-[var(--accent)] bg-emerald-50 text-[var(--accent)]"
                : "border-[var(--border)] bg-[var(--background)] text-[var(--muted)] hover:border-[var(--muted)] hover:text-[var(--foreground)]"
            )}
          >
            All categories
          </button>
          {categories.map((c) => (
            <button
              type="button"
              key={c.slug}
              onClick={() => toggleScrapeCategory(c.slug)}
              className={cn(
                "rounded-lg border px-3 py-2 text-sm font-medium transition",
                CATEGORY_COLORS[c.slug] ?? "border-[var(--border)] bg-[var(--background)] text-[var(--muted)]",
                scrapeCategories.has(c.slug) ? "ring-2 ring-[var(--accent)] ring-offset-2 ring-offset-[var(--background)]" : "hover:opacity-90 opacity-70"
              )}
            >
              {c.name}
            </button>
          ))}
        </div>
      )}
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleClear}
          disabled={clearLoading || loading}
          className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-semibold text-[var(--foreground)] shadow-sm transition hover:bg-[var(--border)] disabled:opacity-50"
        >
          {clearLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : null}
          {clearLoading ? "Clearing…" : "Clear existing data"}
        </button>
        <button
          type="button"
          onClick={handleRun}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
        >
          <Play className="h-4 w-4" aria-hidden />
          {loading ? "Running…" : "Run pipeline now"}
        </button>
      </div>

      {progress && progress.steps.length > 0 && (
        <div className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 text-left shadow-sm">
          <p className="mb-2 text-xs font-medium text-[var(--muted)]">Progress</p>
          <ul className="space-y-1.5">
            {progress.steps.map((step, i) => (
              <li
                key={step.name}
                className="flex items-center gap-2 text-sm"
              >
                {step.status === "success" && (
                  <Check className="h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
                )}
                {step.status === "running" && (
                  <Loader2 className="h-4 w-4 shrink-0 animate-spin text-[var(--accent)]" aria-hidden />
                )}
                {step.status === "pending" && (
                  <Circle className="h-4 w-4 shrink-0 text-[var(--muted)]" aria-hidden />
                )}
                {step.status === "failure" && (
                  <XCircle className="h-4 w-4 shrink-0 text-red-600" aria-hidden />
                )}
                <span
                  className={
                    step.status === "success"
                      ? "text-[var(--muted)]"
                      : step.status === "failure"
                        ? "text-red-600"
                        : "text-[var(--foreground)]"
                  }
                >
                  {step.name}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {message && !progress?.steps.length && (
        <p className="text-right text-xs text-[var(--accent)]">{message}</p>
      )}
      {error && (
        <p className="text-right text-xs text-red-600">{error}</p>
      )}
    </div>
  );
}
