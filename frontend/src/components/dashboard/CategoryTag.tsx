import { CATEGORY_COLORS } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface CategoryTagProps {
  slug: string;
  name: string;
}

export function CategoryTag({ slug, name }: CategoryTagProps) {
  return (
    <span
      className={cn(
        "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium",
        CATEGORY_COLORS[slug] || "border-[var(--border)] bg-[var(--background)] text-[var(--muted)]"
      )}
    >
      {name}
    </span>
  );
}
