import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import { CodeBlock } from "./CodeBlock";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      rehypePlugins={[rehypeRaw]}
      components={{
        code({ node, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const code = String(children).replace(/\n$/, "");
          return match ? (
            <CodeBlock code={code} language={match[1]} />
          ) : (
            <code className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 text-sm" {...props}>
              {children}
            </code>
          );
        },
      }}
      className="markdown-body"
    >
      {content}
    </ReactMarkdown>
  );
}
