import { fetchCategories, fetchStats } from "@/lib/api";
import { FilterBar } from "@/components/dashboard/FilterBar";
import { DashboardContent } from "@/components/dashboard/DashboardContent";
import { TriggerPipelineButton } from "@/components/dashboard/TriggerPipelineButton";
import { StatsStrip } from "@/components/dashboard/StatsStrip";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [categories, stats] = await Promise.all([
    fetchCategories(),
    fetchStats(),
  ]);

  const totalTracked = stats?.total_tracked_repos ?? 0;

  return (
    <div className="space-y-12">
      {/* Hero */}
      <div className="flex flex-col gap-8 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] sm:text-3xl">
            Trending Repositories
          </h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Quality-filtered repos with AI-generated learning content. Run the pipeline to refresh.
          </p>
        </div>
        <TriggerPipelineButton />
      </div>

      <StatsStrip stats={stats} />

      {totalTracked === 0 && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 sm:p-10">
          <div className="mx-auto max-w-lg text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8 4-8-4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-[var(--foreground)]">No data yet</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Click <strong className="text-[var(--foreground)]">Run pipeline now</strong> to ingest trending repos, score them, and generate learning content. Ensure the Celery worker is running and <code className="rounded bg-[var(--surface)] px-1.5 py-0.5 text-xs">GITHUB_TOKEN</code> is set in <code className="rounded bg-[var(--surface)] px-1.5 py-0.5 text-xs">.env</code> for ingestion.
            </p>
          </div>
        </div>
      )}

      {totalTracked > 0 && (
        <div className="space-y-8">
          <FilterBar categories={categories} />
          <DashboardContent />
        </div>
      )}
    </div>
  );
}
