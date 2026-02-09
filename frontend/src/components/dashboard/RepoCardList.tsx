import { RepoCard } from "./RepoCard";
import type { TrendingRepoItem } from "@/lib/types";

interface RepoCardListProps {
  items: TrendingRepoItem[];
  showStarsGained30d?: boolean;
}

export function RepoCardList({ items, showStarsGained30d }: RepoCardListProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] py-16 text-center">
        <p className="text-sm text-[var(--muted)]">
          No trending repos match your filters. Try a different category or sort.
        </p>
      </div>
    );
  }
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      {items.map((item) => (
        <RepoCard key={item.id} item={item} showStarsGained30d={showStarsGained30d} />
      ))}
    </div>
  );
}
