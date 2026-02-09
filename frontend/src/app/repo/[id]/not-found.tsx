import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-4xl mx-auto text-center py-16">
      <h1 className="text-2xl font-bold text-zinc-100">Repository not found</h1>
      <Link href="/" className="mt-4 inline-block text-emerald-400 hover:underline">
        Back to Trending
      </Link>
    </div>
  );
}
