export const CATEGORY_COLORS: Record<string, string> = {
  "ai-ml": "bg-blue-100 text-blue-800 border-blue-200",
  "llms-agents": "bg-violet-100 text-violet-800 border-violet-200",
  "mcp-tooling": "bg-amber-100 text-amber-800 border-amber-200",
  "backend": "bg-emerald-100 text-emerald-800 border-emerald-200",
  "python-libs": "bg-yellow-100 text-yellow-800 border-yellow-200",
  "web3-crypto": "bg-purple-100 text-purple-800 border-purple-200",
  "devops-mlops": "bg-orange-100 text-orange-800 border-orange-200",
};

export const SORT_OPTIONS = [
  { value: "score", label: "Trend score" },
  { value: "recency", label: "Recently pushed" },
  { value: "recent_30d", label: "Stars gained (30d)" },
] as const;
