export interface Stats {
  total_tracked_repos: number;
  repos_passing_quality: number;
  repos_added_today: number;
  content_generated_today: number;
  top_languages: { language: string; count: number }[];
  last_ingestion_at: string | null;
}

export interface CategoryRef {
  slug: string;
  name: string;
}

export interface TrendingRepoItem {
  id: number;
  full_name: string;
  description: string | null;
  stars_count: number;
  stars_delta_24h: number | null;
  stars_gained_30d?: number | null;
  current_trend_score: number | null;
  categories: CategoryRef[];
  topics: string[];
  snippet: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface CategoryItem {
  slug: string;
  name: string;
  description: string | null;
  repo_count: number;
}

export interface ContentBlock {
  markdown: string;
  generated_at: string;
}

export interface TrendHistoryPoint {
  snapshot_at: string;
  stars_count: number;
  stars_delta_24h: number | null;
  computed_trend_score: number | null;
}

export interface RepositoryDetail {
  id: number;
  full_name: string;
  description: string | null;
  html_url: string;
  homepage_url: string | null;
  primary_language: string | null;
  topics: string[];
  license_spdx: string | null;
  stars_count: number;
  forks_count: number;
  open_issues_count: number;
  pushed_at_gh: string;
  current_trend_score: number | null;
  quality_passed: boolean;
  trend_history: TrendHistoryPoint[];
  content: Record<string, ContentBlock>;
}
