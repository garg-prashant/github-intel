import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";
import type { ContentBlock } from "@/lib/types";

interface IntelligenceSectionProps {
  content?: ContentBlock | null;
}

export function IntelligenceSection({ content }: IntelligenceSectionProps) {
  if (!content?.markdown) return null;
  return (
    <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8 shadow-sm">
      <h2 className="mb-5 text-lg font-semibold text-[var(--foreground)]">
        What & Why
      </h2>
      <div className="prose prose-zinc max-w-none">
        <MarkdownRenderer content={content.markdown} />
      </div>
    </section>
  );
}
