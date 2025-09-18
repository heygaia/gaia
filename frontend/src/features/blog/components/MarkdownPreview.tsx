"use client";

import { Card, CardBody, CardHeader } from "@heroui/card";
import { EyeIcon } from "lucide-react";
import Markdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

interface MarkdownPreviewProps {
  content: string;
  title?: string;
}

export function MarkdownPreview({ content, title }: MarkdownPreviewProps) {
  return (
    <Card className="max-h-96 overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <EyeIcon className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-medium">Preview</h3>
        </div>
      </CardHeader>
      <CardBody className="overflow-y-auto pt-0">
        {title && (
          <h1 className="mb-4 text-2xl font-bold text-foreground">{title}</h1>
        )}
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <Markdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              h1: ({ children }) => (
                <h1 className="mb-3 text-xl font-bold text-foreground">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="mt-4 mb-2 text-lg font-semibold text-foreground">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
                  {children}
                </h3>
              ),
              p: ({ children }) => (
                <p className="mb-2 text-sm leading-relaxed text-foreground-600">
                  {children}
                </p>
              ),
              code: ({ children }) => (
                <code className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-xs text-foreground dark:bg-zinc-800">
                  {children}
                </code>
              ),
              pre: ({ children }) => (
                <pre className="mb-2 overflow-x-auto rounded border bg-zinc-100 p-2 text-xs dark:bg-zinc-800">
                  {children}
                </pre>
              ),
              blockquote: ({ children }) => (
                <blockquote className="mb-2 border-l-2 border-zinc-300 pl-2 text-sm text-foreground-600 italic dark:border-zinc-600">
                  {children}
                </blockquote>
              ),
            }}
          >
            {content || "*Start typing to see preview...*"}
          </Markdown>
        </div>
      </CardBody>
    </Card>
  );
}
