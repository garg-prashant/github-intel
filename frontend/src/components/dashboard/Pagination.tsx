"use client";

import { useQueryState } from "nuqs";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  currentPage: number;
  pageSize: number;
  total: number;
}

export function Pagination({ currentPage: page, pageSize, total }: PaginationProps) {
  const [pageParam, setPageParam] = useQueryState("page", { defaultValue: "1" });
  const current = parseInt(pageParam, 10) || page || 1;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const hasPrev = current > 1;
  const hasNext = current < totalPages;

  if (totalPages <= 1) return null;

  return (
    <div className="flex flex-col gap-4 border-t border-[var(--border)] pt-8 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-[var(--muted)]">
        Page <span className="font-medium text-[var(--foreground)]">{current}</span> of{" "}
        <span className="font-medium text-[var(--foreground)]">{totalPages}</span>
        <span className="ml-1">({total.toLocaleString()} repos)</span>
      </p>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => setPageParam(String(current - 1))}
          disabled={!hasPrev}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-medium text-[var(--foreground)] shadow-sm transition disabled:cursor-not-allowed disabled:opacity-40 hover:bg-[var(--background)]"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </button>
        <button
          type="button"
          onClick={() => setPageParam(String(current + 1))}
          disabled={!hasNext}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-medium text-[var(--foreground)] shadow-sm transition disabled:cursor-not-allowed disabled:opacity-40 hover:bg-[var(--background)]"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
