"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MarkdownViewerProps {
  title: string;
  markdown: string | undefined;
  isLoading?: boolean;
}

export function MarkdownViewer({
  title,
  markdown,
  isLoading = false,
}: MarkdownViewerProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-center text-gray-500 p-4">
            Parsing with {title}...
          </div>
        ) : markdown ? (
          <div className="prose dark:prose-invert max-w-none prose-sm">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom table styling
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto">
                    <table
                      className="min-w-full divide-y divide-gray-300 border"
                      {...props}
                    />
                  </div>
                ),
                // Custom code block styling
                code: ({ node, inline, ...props }) =>
                  inline ? (
                    <code
                      className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm"
                      {...props}
                    />
                  ) : (
                    <code
                      className="block p-2 bg-gray-100 dark:bg-gray-800 rounded text-sm overflow-x-auto"
                      {...props}
                    />
                  ),
              }}
            >
              {markdown}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="text-center text-gray-400 p-4 italic">
            No content for this page
          </div>
        )}
      </CardContent>
    </Card>
  );
}
