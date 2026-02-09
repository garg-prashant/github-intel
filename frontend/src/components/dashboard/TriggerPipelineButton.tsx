"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Play, Check, Loader2, Circle, XCircle } from "lucide-react";
import { triggerPipeline, fetchPipelineStatus, type PipelineStatus } from "@/lib/api";

const POLL_INTERVAL_MS = 2500;

export function TriggerPipelineButton() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<PipelineStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const router = useRouter();

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
      const result = await triggerPipeline();
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

  return (
    <div className="flex flex-col items-end gap-3 w-full sm:w-auto">
      <button
        type="button"
        onClick={handleRun}
        disabled={loading}
        className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
      >
        <Play className="h-4 w-4" aria-hidden />
        {loading ? "Running…" : "Run pipeline now"}
      </button>

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
