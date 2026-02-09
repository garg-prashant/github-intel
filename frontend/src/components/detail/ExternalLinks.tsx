import { ExternalLink } from "lucide-react";
import type { RepositoryDetail } from "@/lib/types";

interface ExternalLinksProps {
  repo: RepositoryDetail;
}

export function ExternalLinks({ repo }: ExternalLinksProps) {
  const links = [
    { href: repo.html_url, label: "GitHub" },
    ...(repo.homepage_url ? [{ href: repo.homepage_url, label: "Homepage" }] : []),
  ];
  return (
    <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8 shadow-sm">
      <h2 className="mb-5 text-lg font-semibold text-[var(--foreground)]">
        Links
      </h2>
      <ul className="flex flex-wrap gap-4">
        {links.map(({ href, label }) => (
          <li key={href}>
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 font-medium text-[var(--accent)] transition hover:underline"
            >
              <ExternalLink className="h-4 w-4" aria-hidden />
              {label}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
