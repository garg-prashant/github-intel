import Link from "next/link";
import { Star, TrendingUp } from "lucide-react";
import { TrendDelta } from "./TrendDelta";
import { CategoryTag } from "./CategoryTag";
import type { TrendingRepoItem } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

interface RepoCardProps {
  item: TrendingRepoItem;
  showStarsGained30d?: boolean;
}

export function RepoCard({ item, showStarsGained30d }: RepoCardProps) {
  const show30d = showStarsGained30d && item.stars_gained_30d != null && item.stars_gained_30d > 0;
  const topics = item.topics?.slice(0, 8) ?? [];
  return (
    <Link
      href={`/repo/${item.id}`}
      className="group block rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-sm transition hover:border-[var(--muted)] hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-4">
        <h2 className="min-w-0 flex-1 truncate font-semibold text-[var(--foreground)] group-hover:text-[var(--accent)]">
          {item.full_name}
        </h2>
        <span className="flex shrink-0 items-center gap-1.5 text-sm text-[var(--muted)]">
          <Star className="h-4 w-4 fill-amber-500 text-amber-500" />
          {formatNumber(item.stars_count)}
        </span>
      </div>
      {item.description && (
        <p className="mt-3 line-clamp-2 text-sm text-[var(--muted)] leading-relaxed">
          {item.description}
        </p>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-2.5">
        {show30d && (
          <span className="inline-flex items-center gap-1 rounded-md bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-800">
            <TrendingUp className="h-3 w-3" />
            +{formatNumber(item.stars_gained_30d!)} in 30d
          </span>
        )}
        {item.stars_delta_24h != null && item.stars_delta_24h > 0 && (
          <TrendDelta delta={item.stars_delta_24h} />
        )}
        {item.categories.map((c) => (
          <CategoryTag key={`cat-${c.slug}`} slug={c.slug} name={c.name} />
        ))}
        {topics.map((tag) => (
          <span
            key={`topic-${tag}`}
            className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2.5 py-1 text-xs text-[var(--muted)]"
          >
            {tag}
          </span>
        ))}
      </div>
      {item.snippet && (
        <p className="mt-4 line-clamp-2 border-t border-[var(--border)] pt-3 text-xs text-[var(--muted)] leading-relaxed">
          {item.snippet}
        </p>
      )}
    </Link>
  );
}
