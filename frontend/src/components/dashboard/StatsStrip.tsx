import type { Stats } from "@/lib/types";
import { formatDistanceToNow } from "@/lib/utils";

interface StatsStripProps {
  stats: Stats;
}

export function StatsStrip({ stats }: StatsStripProps) {
  const lastIngestion = stats.last_ingestion_at
    ? formatDistanceToNow(stats.last_ingestion_at)
    : "—";

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-6">
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Tracked repos
        </p>
        <p className="mt-1 text-xl font-semibold tabular-nums text-[var(--foreground)]">
          {stats.total_tracked_repos.toLocaleString()}
        </p>
      </div>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Added today
        </p>
        <p className="mt-1 text-xl font-semibold tabular-nums text-[var(--foreground)]">
          {stats.repos_added_today.toLocaleString()}
        </p>
      </div>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Content today
        </p>
        <p className="mt-1 text-xl font-semibold tabular-nums text-[var(--foreground)]">
          {stats.content_generated_today.toLocaleString()}
        </p>
      </div>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Last ingestion
        </p>
        <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
          {lastIngestion}
        </p>
      </div>
    </div>
  );
}
