"use client";

import { useQueryState } from "nuqs";
import { CATEGORY_COLORS, SORT_OPTIONS } from "@/lib/constants";
import type { CategoryItem } from "@/lib/types";
import { cn } from "@/lib/utils";

interface FilterBarProps {
  categories: CategoryItem[];
}

const QUALITY_OPTIONS = [
  { value: "passed", label: "Passing quality" },
  { value: "all", label: "All repos" },
  { value: "not_passed", label: "Didn't pass quality" },
] as const;

export function FilterBar({ categories }: FilterBarProps) {
  const [category, setCategory] = useQueryState("category", { defaultValue: "" });
  const [sortBy, setSortBy] = useQueryState("sort_by", { defaultValue: "score" });
  const [quality, setQuality] = useQueryState("quality", { defaultValue: "passed" });
  const [, setPage] = useQueryState("page");

  const handleCategoryChange = (slug: string) => {
    setCategory(slug || null);
    setPage("1");
  };

  const handleSortChange = (value: string) => {
    setSortBy(value);
    setPage("1");
  };

  const handleQualityChange = (value: string) => {
    setQuality(value);
    setPage("1");
  };

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">
      <div className="flex flex-wrap items-center gap-4 sm:gap-6">
        <span className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Category
        </span>
        <div className="flex flex-wrap gap-2.5">
        <button
          type="button"
          onClick={() => handleCategoryChange("")}
          className={cn(
            "rounded-lg border px-3 py-2 text-sm font-medium transition",
            !category
              ? "border-[var(--accent)] bg-emerald-50 text-[var(--accent)]"
              : "border-[var(--border)] bg-[var(--background)] text-[var(--muted)] hover:border-[var(--muted)] hover:text-[var(--foreground)]"
          )}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            type="button"
            key={c.slug}
            onClick={() => handleCategoryChange(c.slug)}
            className={cn(
              "rounded-lg border px-3 py-2 text-sm font-medium transition",
              CATEGORY_COLORS[c.slug] ?? "border-[var(--border)] bg-[var(--background)] text-[var(--muted)]",
              category === c.slug ? "ring-2 ring-[var(--accent)] ring-offset-2 ring-offset-[var(--background)]" : "hover:opacity-90"
            )}
          >
            {c.name}
          </button>
        ))}
        </div>
        <span className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Quality
        </span>
        <div className="inline-flex rounded-lg border border-[var(--border)] bg-[var(--background)] p-1">
          {QUALITY_OPTIONS.map((opt) => (
            <button
              type="button"
              key={opt.value}
              onClick={() => handleQualityChange(opt.value)}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium transition",
                quality === opt.value
                  ? "bg-[var(--surface)] text-[var(--foreground)] shadow-sm border border-[var(--border)]"
                  : "text-[var(--muted)] hover:text-[var(--foreground)]"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <span className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Sort
        </span>
        <div className="inline-flex rounded-lg border border-[var(--border)] bg-[var(--background)] p-1">
          {SORT_OPTIONS.map((opt) => (
            <button
              type="button"
              key={opt.value}
              onClick={() => handleSortChange(opt.value)}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium transition",
                sortBy === opt.value
                  ? "bg-[var(--surface)] text-[var(--foreground)] shadow-sm border border-[var(--border)]"
                  : "text-[var(--muted)] hover:text-[var(--foreground)]"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
