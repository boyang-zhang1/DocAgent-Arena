"use client";

import { useState } from "react";

interface PDFViewerProps {
  fileId: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  onLoadSuccess?: (numPages: number) => void;
}

export function PDFViewer({
  fileId,
  currentPage,
  onPageChange,
  onLoadSuccess,
}: PDFViewerProps) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const pdfUrl = `${apiUrl}/api/v1/parse/file/${fileId}`;

  return (
    <div className="border rounded-lg p-4 bg-gray-50 dark:bg-gray-900">
      <div className="mb-2 text-sm text-gray-600 dark:text-gray-400">
        Original PDF - Page {currentPage}
      </div>
      <div className="flex justify-center">
        <iframe
          src={pdfUrl}
          className="w-full h-[600px] border-0"
          title="PDF Viewer"
        />
      </div>
    </div>
  );
}
