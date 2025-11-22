"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { FileUploadZone } from "@/components/parse/FileUploadZone";
import { ProviderConfigForm } from "@/components/parse/ProviderConfigForm";
import { PDFViewer } from "@/components/parse/PDFViewer";
import { MarkdownViewer } from "@/components/parse/MarkdownViewer";
import { CostDisplay } from "@/components/parse/CostDisplay";
import { CostEstimation } from "@/components/parse/CostEstimation";
import { ProcessingTimeDisplay } from "@/components/parse/ProcessingTimeDisplay";
import { PageNavigator } from "@/components/parse/PageNavigator";
import { ProviderLabel } from "@/components/providers/ProviderLabel";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ContactIcons } from "@/components/ui/ContactIcons";
import { FileText, Loader2, CheckCircle2, XCircle, ChevronLeft, ChevronRight } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { getProviderDisplayName } from "@/lib/providerMetadata";
import type { LlamaIndexConfig, ReductoConfig, LandingAIConfig } from "@/types/api";
import { useProviderPricing } from "@/hooks/useProviderPricing";
import { usePDFViewer } from "@/hooks/usePDFViewer";

interface PageData {
  page_number: number;
  markdown: string;
  images: string[];
  metadata: Record<string, any>;
}

interface ProviderResult {
  total_pages: number;
  pages: PageData[];
  processing_time: number;
  usage: Record<string, any>;
}

interface ParseResults {
  [provider: string]: ProviderResult;
}

interface CostData {
  provider: string;
  credits: number;
  usd_per_credit: number;
  total_usd: number;
  details: Record<string, any>;
}

interface CostResults {
  [provider: string]: CostData;
}

interface ProviderConfigs {
  llamaindex?: LlamaIndexConfig;
  reducto?: ReductoConfig;
  landingai?: LandingAIConfig;
}

function ParsePageContent() {
  const searchParams = useSearchParams();
  const debugMode = searchParams.get("mode") === "debug";

  // PDF Viewer state (using shared hook)
  const {
    fileId,
    pdfFile,
    currentPage,
    totalPages,
    setFileId,
    setPdfFile,
    handlePageChange,
    handleLoadSuccess,
    handleFileUpload,
    extractCurrentPageAsBlob,
    reset: resetPdfViewer,
  } = usePDFViewer();

  const [selectedProviders, setSelectedProviders] = useState<string[]>([
    "llamaindex",
    "reducto",
    "landingai",
  ]);
  const [providerConfigs, setProviderConfigs] = useState<ProviderConfigs>({});
  const [fileName, setFileName] = useState<string>("");
  const [parseMode, setParseMode] = useState<'single' | 'full'>('single');
  const [parseResults, setParseResults] = useState<ParseResults | null>(null);
  const [costResults, setCostResults] = useState<CostResults | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingPageCount, setIsLoadingPageCount] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [providerStatus, setProviderStatus] = useState<Record<string, 'pending' | 'running' | 'completed' | 'error'>>({});
  const [displayedProviders, setDisplayedProviders] = useState<string[]>([]);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [enableLatex, setEnableLatex] = useState(false);

  const { pricingMap, loading: pricingLoading, error: pricingError } = useProviderPricing();

  const handleSelectionChange = (selected: string[]) => {
    setSelectedProviders(selected);
  };

  const handleConfigsChange = (configs: ProviderConfigs) => {
    setProviderConfigs(configs);
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);

    try {
      const data = await apiClient.uploadPdf(file);
      setFileName(data.filename);

      // Get page count instead of auto-parsing
      setIsLoadingPageCount(true);
      try {
        const pageCountData = await apiClient.getPageCount(data.file_id);
        handleFileUpload(data.file_id, file, pageCountData.page_count);
      } catch (err) {
        console.error("Page count error:", err);
        setError(err instanceof Error ? err.message : "Failed to get page count");
      } finally {
        setIsLoadingPageCount(false);
      }
    } catch (err) {
      console.error("Upload error:", err);
      setError(err instanceof Error ? err.message : "Failed to upload file");
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirmParse = async () => {
    if (!fileId) return;

    setIsParsing(true);
    setError(null);
    setProviderStatus({});

    try {
      let parseFileId = fileId;
      let parseFileName = fileName;

      // If single-page mode, extract and upload the current page
      if (parseMode === 'single') {
        const singlePageBlob = await extractCurrentPageAsBlob();
        if (!singlePageBlob) {
          throw new Error("Failed to extract current page");
        }

        // Convert blob to File for upload
        const singlePageFile = new File(
          [singlePageBlob],
          `${fileName.replace('.pdf', '')}_page_${currentPage}.pdf`,
          { type: 'application/pdf' }
        );

        // Upload the single-page PDF
        const uploadResponse = await apiClient.uploadPdf(singlePageFile);
        parseFileId = uploadResponse.file_id;
        parseFileName = uploadResponse.filename;
      }

      // Prepare configs for selected providers
      const configs: Record<string, any> = {};
      selectedProviders.forEach((provider) => {
        if (providerConfigs[provider as keyof ProviderConfigs]) {
          configs[provider] = providerConfigs[provider as keyof ProviderConfigs];
        }
      });

      // Use streaming API with progress callback
      const data = await apiClient.compareParsesStream(
        {
          fileId: parseFileId,
          providers: selectedProviders,
          configs,
          filename: parseFileName || undefined,
          debug: debugMode,
        },
        (event) => {
          // Handle progress events
          if (event.type === 'started') {
            // Initialize all providers as running
            const initialStatus: Record<string, 'running'> = {};
            event.data.providers.forEach((provider: string) => {
              initialStatus[provider] = 'running';
            });
            setProviderStatus(initialStatus);
          } else if (event.type === 'progress') {
            // Provider completed
            setProviderStatus(prev => ({
              ...prev,
              [event.data.provider]: 'completed'
            }));
          } else if (event.type === 'error') {
            // Provider failed
            setProviderStatus(prev => ({
              ...prev,
              [event.data.provider]: 'error'
            }));
          }
        }
      );

      setParseResults(data.results);

      // Initialize displayed providers (all by default)
      setDisplayedProviders(Object.keys(data.results));
      setCarouselIndex(0);

      // Calculate costs
      try {
        const costData = await apiClient.calculateParseCost(data);
        setCostResults(costData.costs);
      } catch (costErr) {
        console.error("Cost calculation error:", costErr);
        // Don't fail the entire parse if cost calculation fails
      }
    } catch (err) {
      console.error("Parse error:", err);
      setError(err instanceof Error ? err.message : "Failed to parse PDF");
    } finally {
      setIsParsing(false);
    }
  };

  const handleReset = () => {
    resetPdfViewer();
    setFileName("");
    setParseResults(null);
    setCostResults(null);
    setError(null);
  };

  // Get markdown for a specific provider and page
  const getProviderMarkdown = (provider: string) => {
    if (!parseResults?.[provider]) return undefined;
    // In single-page mode, the extracted page is always page 1 in the results
    const pageNumber = parseMode === 'single' ? 1 : currentPage;
    const page = parseResults[provider].pages.find(
      (p) => p.page_number === pageNumber
    );
    return page?.markdown;
  };

  // Get metadata for a specific provider and page
  const getProviderMetadata = (provider: string) => {
    if (!parseResults?.[provider]) return undefined;
    // In single-page mode, the extracted page is always page 1 in the results
    const pageNumber = parseMode === 'single' ? 1 : currentPage;
    const page = parseResults[provider].pages.find(
      (p) => p.page_number === pageNumber
    );
    return page?.metadata;
  };

  // Get list of providers that were run (have results)
  const runProviders = parseResults ? Object.keys(parseResults) : [];

  // Toggle provider display
  const toggleProviderDisplay = (provider: string) => {
    setDisplayedProviders((prev) => {
      if (prev.includes(provider)) {
        // Remove provider
        const newProviders = prev.filter((p) => p !== provider);
        // Reset carousel if needed
        if (newProviders.length <= 3) {
          setCarouselIndex(0);
        } else if (carouselIndex > newProviders.length - 3) {
          setCarouselIndex(Math.max(0, newProviders.length - 3));
        }
        return newProviders;
      } else {
        // Add provider (maintain order from runProviders)
        const newProviders = runProviders.filter(
          (p) => prev.includes(p) || p === provider
        );
        return newProviders;
      }
    });
  };

  // Carousel navigation
  const canGoPrev = carouselIndex > 0;
  const canGoNext = displayedProviders.length > 3 && carouselIndex < displayedProviders.length - 3;

  const handlePrevPage = () => {
    if (canGoPrev) {
      setCarouselIndex(carouselIndex - 1);
    }
  };

  const handleNextPage = () => {
    if (canGoNext) {
      setCarouselIndex(carouselIndex + 1);
    }
  };

  // Get providers to display in carousel (max 3 at a time)
  const visibleProviders = displayedProviders.length <= 3
    ? displayedProviders
    : displayedProviders.slice(carouselIndex, carouselIndex + 3);

  return (
    <div className="container mx-auto p-6 max-w-full px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">PDF Parse & Compare</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Upload a PDF to compare parsing results from LlamaIndex, Reducto, and
          LandingAI
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Provider Configuration */}
      <div className="mb-6">
        <ProviderConfigForm
          onConfigsChange={handleConfigsChange}
          onSelectionChange={handleSelectionChange}
          disabled={isUploading || isParsing}
          pricing={pricingMap}
          pricingLoading={pricingLoading}
          pricingError={pricingError}
        />
      </div>

      {!fileId ? (
        <div className="max-w-2xl mx-auto">
          <FileUploadZone
            onUpload={handleUpload}
            disabled={selectedProviders.length === 0}
          />
          {selectedProviders.length === 0 && (
            <p className="mt-4 text-center text-sm text-gray-500">
              Please select at least one provider above to enable upload
            </p>
          )}
          {isUploading && (
            <div className="mt-4 text-center text-gray-600 flex items-center justify-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploading and analyzing...
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Header with file info and reset button */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-gray-500" />
              <span className="font-medium">{fileName}</span>
              {totalPages > 0 && (
                <span className="text-sm text-gray-500">
                  ({totalPages} {totalPages === 1 ? "page" : "pages"})
                </span>
              )}
            </div>
            <Button variant="outline" onClick={handleReset}>
              Upload New File
            </Button>
          </div>

          {/* Loading page count */}
          {isLoadingPageCount && (
            <div className="text-center py-6">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-blue-500" />
              <p className="text-sm text-gray-500">Analyzing PDF...</p>
            </div>
          )}

          {/* PDF Viewer - Show immediately after page count loads */}
          {totalPages > 0 && !isLoadingPageCount && (
            <>
              <div className="max-w-4xl mx-auto">
                <PDFViewer
                  fileId={fileId}
                  pdfFile={pdfFile || undefined}
                  currentPage={currentPage}
                  onPageChange={handlePageChange}
                  onLoadSuccess={handleLoadSuccess}
                />
              </div>

              {/* Page Navigator - Below PDF */}
              <PageNavigator
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </>
          )}

          {/* Parse Mode Selection - Show after page count is loaded but before parsing */}
          {totalPages > 0 && !isLoadingPageCount && !parseResults && !isParsing && (
            <div className="max-w-2xl mx-auto space-y-4">
              {/* Parse Mode Toggle */}
              <div className="bg-blue-50 dark:bg-blue-950/30 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="parse-full-pdf"
                    checked={parseMode === 'full'}
                    onCheckedChange={(checked) => setParseMode(checked ? 'full' : 'single')}
                  />
                  <div className="flex-1">
                    <label
                      htmlFor="parse-full-pdf"
                      className="text-sm font-medium cursor-pointer text-gray-700 dark:text-gray-300"
                    >
                      Parse entire PDF
                    </label>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {parseMode === 'single' ? (
                        <>
                          Currently: <span className="font-medium">Single page mode</span> - Only page {currentPage} will be parsed (faster & cheaper)
                        </>
                      ) : (
                        <>
                          Currently: <span className="font-medium">Full PDF mode</span> - All {totalPages} pages will be parsed
                        </>
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {/* Cost Estimation */}
              <CostEstimation
                pageCount={parseMode === 'single' ? 1 : totalPages}
                providers={selectedProviders}
                configs={providerConfigs}
                onConfirm={handleConfirmParse}
                disabled={isParsing}
                pricing={pricingMap}
                pricingLoading={pricingLoading}
                pricingError={pricingError}
              />
            </div>
          )}

          {/* Parsing Status */}
          {isParsing && (
            <div className="max-w-2xl mx-auto py-12">
              <div className="text-center mb-8">
                <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-blue-500" />
                <p className="text-lg font-medium">Parsing PDF...</p>
                <p className="text-sm text-gray-500 mt-2">
                  {parseMode === 'single' ? (
                    <>Parsing page {currentPage} of {totalPages}</>
                  ) : (
                    <>Parsing all {totalPages} pages - this may take a few moments</>
                  )}
                </p>
              </div>

              {/* Provider Progress List */}
              <div className="space-y-3 bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                  Provider Status:
                </p>
                {Object.entries(providerStatus).map(([provider, status]) => (
                  <div
                    key={provider}
                    className="flex items-center justify-between p-3 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex items-center gap-3">
                      <ProviderLabel provider={provider} size={20} />
                    </div>
                    <div className="flex items-center gap-2">
                      {status === 'running' && (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            Running...
                          </span>
                        </>
                      )}
                      {status === 'completed' && (
                        <>
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                          <span className="text-sm text-green-600 dark:text-green-400">
                            Completed
                          </span>
                        </>
                      )}
                      {status === 'error' && (
                        <>
                          <XCircle className="h-4 w-4 text-red-500" />
                          <span className="text-sm text-red-600 dark:text-red-400">
                            Failed
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Results Section - Show below PDF viewer when parsing completes */}
          {parseResults && (
            <>
              {/* Provider Selection Checkboxes */}
              {runProviders.length > 1 && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-6 flex-wrap">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Select Providers:
                    </span>
                    {runProviders.map((provider) => (
                      <div key={provider} className="flex items-center gap-2">
                        <Checkbox
                          id={`provider-${provider}`}
                          checked={displayedProviders.includes(provider)}
                          onCheckedChange={() => toggleProviderDisplay(provider)}
                        />
                        <label
                          htmlFor={`provider-${provider}`}
                          className="cursor-pointer"
                        >
                          <ProviderLabel provider={provider} size={20} />
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Render Options */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-6 flex-wrap">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Render Options:
                  </span>
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="enable-latex"
                      checked={enableLatex}
                      onCheckedChange={(checked) => setEnableLatex(checked === true)}
                    />
                    <label
                      htmlFor="enable-latex"
                      className="text-sm cursor-pointer text-gray-600 dark:text-gray-400"
                    >
                      Enable LaTeX formula rendering ($...$)
                    </label>
                  </div>
                </div>
              </div>

              {/* Carousel Navigation */}
              {displayedProviders.length > 3 && (
                <div className="flex items-center justify-center gap-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePrevPage}
                    disabled={!canGoPrev}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Showing {carouselIndex + 1}-{Math.min(carouselIndex + 3, displayedProviders.length)} of {displayedProviders.length}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleNextPage}
                    disabled={!canGoNext}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              )}

              {/* Provider Comparison - Dynamic columns based on number of visible providers */}
              <div
                className={`grid gap-8 ${
                  visibleProviders.length === 1
                    ? "grid-cols-1 max-w-4xl mx-auto"
                    : visibleProviders.length === 2
                    ? "grid-cols-1 md:grid-cols-2"
                    : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
                }`}
              >
                {visibleProviders.map((provider) => (
                  <div key={provider} className="space-y-4">
                    <MarkdownViewer
                      title={
                        <ProviderLabel
                          provider={provider}
                          size={26}
                          className="gap-2"
                        />
                      }
                      markdown={getProviderMarkdown(provider)}
                      metadata={getProviderMetadata(provider)}
                      provider={provider}
                      disableMathRendering={!enableLatex}
                    />

                    {/* Info Cards Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      {/* Processing Time Card */}
                      <ProcessingTimeDisplay
                        processingTime={
                          parseResults[provider]?.processing_time || 0
                        }
                        providerName={getProviderDisplayName(provider)}
                      />

                      {/* Cost Card */}
                      {costResults && costResults[provider] && (
                        <CostDisplay
                          cost={costResults[provider]}
                          providerName={getProviderDisplayName(provider)}
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      <ContactIcons />
    </div>
  );
}

export default function ParsePage() {
  return (
    <Suspense fallback={<div className="container mx-auto p-6 text-center">Loading...</div>}>
      <ParsePageContent />
    </Suspense>
  );
}
