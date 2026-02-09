const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const defaultOptions: RequestInit = {
  next: { revalidate: 3600 },
};

export async function fetchTrendingRepos(params: {
  category?: string;
  sort_by?: string;
  language?: string;
  page?: number;
  page_size?: number;
}): Promise<{ items: import("./types").TrendingRepoItem[]; page: number; page_size: number; total: number }> {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.sort_by) search.set("sort_by", params.sort_by);
  if (params.language) search.set("language", params.language);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const res = await fetch(`${API_URL}/api/v1/trending?${search}`, defaultOptions);
  if (!res.ok) throw new Error("Failed to fetch trending");
  return res.json();
}

export async function fetchCategories(): Promise<import("./types").CategoryItem[]> {
  const res = await fetch(`${API_URL}/api/v1/categories`, defaultOptions);
  if (!res.ok) throw new Error("Failed to fetch categories");
  return res.json();
}

export async function fetchStats(): Promise<import("./types").Stats> {
  const res = await fetch(`${API_URL}/api/v1/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function fetchRepository(id: number): Promise<import("./types").RepositoryDetail> {
  const res = await fetch(`${API_URL}/api/v1/repositories/${id}`, defaultOptions);
  if (!res.ok) throw new Error("Failed to fetch repository");
  return res.json();
}

export async function triggerPipeline(): Promise<{ started: boolean; message: string; chain_id?: string }> {
  const res = await fetch(`${API_URL}/api/v1/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to trigger pipeline");
  }
  return res.json();
}

export async function clearExistingData(): Promise<{ deleted: number; message: string }> {
  const res = await fetch(`${API_URL}/api/v1/pipeline/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to clear data");
  }
  return res.json();
}

export interface PipelineStepStatus {
  name: string;
  status: "pending" | "running" | "success" | "failure";
}

export interface PipelineStatus {
  chain_id: string;
  status: "running" | "success" | "failure";
  current_step_index: number | null;
  steps: PipelineStepStatus[];
  error: string | null;
}

export async function fetchPipelineStatus(chainId: string): Promise<PipelineStatus> {
  const res = await fetch(`${API_URL}/api/v1/pipeline/status/${encodeURIComponent(chainId)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch pipeline status");
  return res.json();
}
