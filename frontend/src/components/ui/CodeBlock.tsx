import { CopyButton } from "./CopyButton";

interface CodeBlockProps {
  code: string;
  language: string;
}

export async function CodeBlock({ code, language }: CodeBlockProps) {
  // Optional: use Shiki for server-side highlighting. For simplicity we use a pre/code block.
  return (
    <div className="relative rounded-lg bg-zinc-900 border border-zinc-800 overflow-hidden my-4">
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800 text-zinc-400 text-xs">
        <span>{language}</span>
        <CopyButton text={code} />
      </div>
      <pre className="p-4 overflow-x-auto text-sm">
        <code className="text-zinc-300">{code}</code>
      </pre>
    </div>
  );
}
