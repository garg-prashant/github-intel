"use client";

import { useEffect, useState } from "react";
import { useQueryState } from "nuqs";
import { fetchTrendingRepos } from "@/lib/api";
import type { PaginatedResponse, TrendingRepoItem } from "@/lib/types";
import { RepoCardList } from "./RepoCardList";
import { Pagination } from "./Pagination";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function clientFetchTrending(params: {
  category?: string;
  sort_by?: string;
  language?: string;
  quality?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<TrendingRepoItem>> {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.language) search.set("language", params.language);
  if (params.quality && params.quality !== "passed") search.set("quality", params.quality);
  const sortBy = params.sort_by ?? "score";
  if (sortBy === "recent_30d") {
    search.set("mode", "recent");
    search.set("sort_by", "score");
  } else {
    search.set("mode", "overall");
    search.set("sort_by", sortBy);
  }
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size ?? 20));
  const res = await fetch(`${API_URL}/api/v1/trending?${search}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch trending");
  return res.json();
}

function ListSkeleton() {
  return (
    <div className="grid gap-6 sm:grid-cols-2" aria-busy="true">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 animate-pulse"
        >
          <div className="mb-3 h-5 w-3/4 rounded bg-[var(--muted)]/30" />
          <div className="mb-4 h-3 w-1/2 rounded bg-[var(--muted)]/20" />
          <div className="space-y-2.5">
            <div className="h-3 w-full rounded bg-[var(--muted)]/15" />
            <div className="h-3 w-4/5 rounded bg-[var(--muted)]/15" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DashboardContent() {
  const [category] = useQueryState("category", { defaultValue: "" });
  const [sortBy] = useQueryState("sort_by", { defaultValue: "score" });
  const [quality] = useQueryState("quality", { defaultValue: "passed" });
  const [pageParam] = useQueryState("page", { defaultValue: "1" });
  const page = Math.max(1, parseInt(pageParam || "1", 10));

  const [data, setData] = useState<PaginatedResponse<TrendingRepoItem> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    clientFetchTrending({
      category: category || undefined,
      sort_by: sortBy,
      quality: quality || "passed",
      page,
      page_size: 20,
    })
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load repos");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [category, sortBy, quality, page]);

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <ListSkeleton />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <RepoCardList
        items={data.items}
        showStarsGained30d={sortBy === "recent_30d"}
      />
      <Pagination
        currentPage={data.page}
        pageSize={data.page_size}
        total={data.total}
      />
    </div>
  );
}
