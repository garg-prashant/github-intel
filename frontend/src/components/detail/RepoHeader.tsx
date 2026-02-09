import Link from "next/link";
import { Star, GitFork, Circle, ArrowLeft } from "lucide-react";
import type { RepositoryDetail } from "@/lib/types";
import { formatNumber, relativeTime } from "@/lib/utils";
import { CategoryTag } from "@/components/dashboard/CategoryTag";

interface RepoHeaderProps {
  repo: RepositoryDetail;
}

export function RepoHeader({ repo }: RepoHeaderProps) {
  return (
    <header className="space-y-5">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--muted)] transition hover:text-[var(--foreground)]"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Back to trending
      </Link>
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] sm:text-3xl">
          {repo.full_name}
        </h1>
        {repo.description && (
          <p className="mt-2 text-[var(--muted)]">{repo.description}</p>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-[var(--muted)]">
        <span className="inline-flex items-center gap-1">
          <Star className="h-4 w-4 fill-amber-500 text-amber-500" />
          {formatNumber(repo.stars_count)}
        </span>
        <span className="inline-flex items-center gap-1">
          <GitFork className="h-4 w-4" />
          {repo.forks_count} forks
        </span>
        {repo.primary_language && (
          <span className="inline-flex items-center gap-1">
            <Circle className="h-2 w-2 fill-[var(--accent)]" />
            {repo.primary_language}
          </span>
        )}
        <span>Updated {relativeTime(repo.pushed_at_gh)}</span>
        {repo.license_spdx && (
          <span>{repo.license_spdx}</span>
        )}
      </div>
      {repo.topics.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {repo.topics.map((t) => (
            <span
              key={t}
              className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2.5 py-1 text-xs font-medium text-[var(--muted)]"
            >
              {t}
            </span>
          ))}
        </div>
      )}
    </header>
  );
}
