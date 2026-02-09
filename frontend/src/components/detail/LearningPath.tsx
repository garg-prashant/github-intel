import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";
import type { ContentBlock } from "@/lib/types";

interface LearningPathProps {
  content?: ContentBlock | null;
}

export function LearningPath({ content }: LearningPathProps) {
  if (!content?.markdown) return null;
  return (
    <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8 shadow-sm">
      <h2 className="mb-5 text-lg font-semibold text-[var(--foreground)]">
        Learning Path
      </h2>
      <div className="prose prose-zinc max-w-none">
        <MarkdownRenderer content={content.markdown} />
      </div>
    </section>
  );
}
