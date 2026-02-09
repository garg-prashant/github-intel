import type { Stats } from "@/lib/types";
import { formatDistanceToNow } from "@/lib/utils";

interface StatsStripProps {
  stats: Stats | null | undefined;
}

export function StatsStrip({ stats }: StatsStripProps) {
  const lastIngestion = stats?.last_ingestion_at
    ? formatDistanceToNow(stats.last_ingestion_at)
    : "—";
  // Tracked = repos shown on dashboard (quality_passed). Don't fall back to total or card won't match list.
  const passing = stats?.repos_passing_quality ?? 0;
  const total = stats?.total_tracked_repos ?? 0;
  const addedToday = stats?.repos_added_today ?? 0;
  const contentToday = stats?.content_generated_today ?? 0;

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-6">
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Passing quality
        </p>
        <p className="mt-1 text-xl font-semibold tabular-nums text-[var(--foreground)]">
          {passing.toLocaleString()}
        </p>
        {total > 0 && (
          <p className="mt-0.5 text-xs text-[var(--muted)]">
            {total} total in DB
          </p>
        )}
      </div>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          First seen today
        </p>
        <p className="mt-1 text-xl font-semibold tabular-nums text-[var(--foreground)]">
          {addedToday.toLocaleString()}
        </p>
      </div>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Content today
        </p>
        <p className="mt-1 text-xl font-semibold tabular-nums text-[var(--foreground)]">
          {contentToday.toLocaleString()}
        </p>
      </div>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Last snapshot
        </p>
        <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
          {lastIngestion}
        </p>
      </div>
    </div>
  );
}
