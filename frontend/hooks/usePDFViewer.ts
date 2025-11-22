import { useState, useCallback } from "react";
import { PDFDocument } from "pdf-lib";

interface UsePDFViewerOptions {
  /**
   * Initial page number (default: 1)
   */
  initialPage?: number;
}

export interface UsePDFViewerReturn {
  // State
  fileId: string | null;
  pdfFile: File | null;
  currentPage: number;
  totalPages: number;

  // Setters
  setFileId: (id: string | null) => void;
  setPdfFile: (file: File | null) => void;
  setCurrentPage: (page: number) => void;
  setTotalPages: (pages: number) => void;

  // Handlers
  handlePageChange: (page: number) => void;
  handleLoadSuccess: (numPages: number) => void;
  handleFileUpload: (fileId: string, file: File, pageCount?: number) => void;

  // Utils
  extractCurrentPageAsBlob: () => Promise<Blob | null>;
  reset: () => void;
}

/**
 * Shared hook for PDF viewer state management.
 * Consolidates common logic between battle page and parse page.
 */
export function usePDFViewer(options: UsePDFViewerOptions = {}): UsePDFViewerReturn {
  const { initialPage = 1 } = options;

  const [fileId, setFileId] = useState<string | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(0);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  const handleLoadSuccess = useCallback((numPages: number) => {
    setTotalPages(numPages);
  }, []);

  const handleFileUpload = useCallback((
    uploadedFileId: string,
    file: File,
    pageCount?: number
  ) => {
    setFileId(uploadedFileId);
    setPdfFile(file);
    setCurrentPage(initialPage);
    if (pageCount !== undefined) {
      setTotalPages(pageCount);
    }
  }, [initialPage]);

  /**
   * Extracts the current page from the PDF as a single-page PDF blob.
   * Useful for submitting only the current page to parsing services.
   */
  const extractCurrentPageAsBlob = useCallback(async (): Promise<Blob | null> => {
    if (!pdfFile) {
      console.warn("No PDF file loaded");
      return null;
    }

    try {
      // Load the full PDF
      const pdfBytes = await pdfFile.arrayBuffer();
      const pdfDoc = await PDFDocument.load(pdfBytes);

      // Create new PDF with only current page
      const singlePagePdf = await PDFDocument.create();
      const pageIndex = currentPage - 1; // Convert to 0-indexed

      if (pageIndex < 0 || pageIndex >= pdfDoc.getPageCount()) {
        throw new Error(`Page ${currentPage} is out of range`);
      }

      const [copiedPage] = await singlePagePdf.copyPages(pdfDoc, [pageIndex]);
      singlePagePdf.addPage(copiedPage);

      // Save as blob
      const singlePageBytes = await singlePagePdf.save();
      const blob = new Blob([new Uint8Array(singlePageBytes)], { type: "application/pdf" });

      return blob;
    } catch (error) {
      console.error("Failed to extract page:", error);
      return null;
    }
  }, [pdfFile, currentPage]);

  const reset = useCallback(() => {
    setFileId(null);
    setPdfFile(null);
    setCurrentPage(initialPage);
    setTotalPages(0);
  }, [initialPage]);

  return {
    // State
    fileId,
    pdfFile,
    currentPage,
    totalPages,

    // Setters
    setFileId,
    setPdfFile,
    setCurrentPage,
    setTotalPages,

    // Handlers
    handlePageChange,
    handleLoadSuccess,
    handleFileUpload,

    // Utils
    extractCurrentPageAsBlob,
    reset,
  };
}
