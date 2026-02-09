export default function Loading() {
  return (
    <div className="mx-auto max-w-4xl space-y-8 animate-pulse">
      <div className="h-5 w-32 rounded bg-[var(--surface)]" />
      <div className="h-10 w-3/4 rounded bg-[var(--surface)]" />
      <div className="h-4 w-full rounded bg-[var(--surface)]" />
      <div className="h-24 rounded-xl bg-[var(--surface)]" />
      <div className="h-48 rounded-xl bg-[var(--surface)]" />
    </div>
  );
}
