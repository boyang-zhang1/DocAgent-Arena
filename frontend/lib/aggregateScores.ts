import { DocumentResult, ProviderResult, RunDetail } from '@/types/api';

/**
 * Overall aggregate scores for a single provider across all documents
 */
export interface ProviderOverallScores {
  provider: string;
  averageScores: Record<string, number>;  // metric -> average value
  averageDuration: number | null;
  successRate: number;  // 0-1, percentage of successful documents
  totalDocuments: number;
  successfulDocuments: number;
}

/**
 * Calculate overall aggregate scores for all providers in a benchmark run
 *
 * Aggregates per-document scores to create run-level averages for each provider.
 * Only includes successful provider results in calculations.
 */
export function calculateOverallScores(
  documents: DocumentResult[],
  providerNames: string[]
): ProviderOverallScores[] {
  const results: ProviderOverallScores[] = [];

  providerNames.forEach(providerName => {
    const metricSums: Record<string, number> = {};
    const metricCounts: Record<string, number> = {};
    const durations: number[] = [];
    let successfulDocs = 0;
    let totalDocs = 0;

    // Aggregate across all documents
    documents.forEach(doc => {
      const providerResult = doc.providers[providerName];
      if (!providerResult) return;

      totalDocs++;

      // Only include successful results in metric calculations
      if (providerResult.status === 'success' && providerResult.aggregated_scores) {
        successfulDocs++;

        // Aggregate scores
        Object.entries(providerResult.aggregated_scores).forEach(([metric, value]) => {
          if (typeof value === 'number' && !isNaN(value)) {
            if (!metricSums[metric]) {
              metricSums[metric] = 0;
              metricCounts[metric] = 0;
            }
            metricSums[metric] += value;
            metricCounts[metric]++;
          }
        });

        // Collect durations
        if (providerResult.duration_seconds !== null) {
          durations.push(providerResult.duration_seconds);
        }
      }
    });

    // Calculate averages
    const averageScores: Record<string, number> = {};
    Object.keys(metricSums).forEach(metric => {
      averageScores[metric] = metricSums[metric] / metricCounts[metric];
    });

    const averageDuration = durations.length > 0
      ? durations.reduce((sum, d) => sum + d, 0) / durations.length
      : null;

    const successRate = totalDocs > 0 ? successfulDocs / totalDocs : 0;

    results.push({
      provider: providerName,
      averageScores,
      averageDuration,
      successRate,
      totalDocuments: totalDocs,
      successfulDocuments: successfulDocs,
    });
  });

  return results;
}

/**
 * Sort providers by a specific metric (descending - higher is better)
 * Falls back to provider name if metric is not available
 */
export function sortProvidersByMetric(
  providers: ProviderOverallScores[],
  metricName?: string
): ProviderOverallScores[] {
  // If no metric specified, try to find a common one
  if (!metricName) {
    // Try common metrics in order of preference
    const commonMetrics = ['factual_correctness(mode=f1)', 'faithfulness', 'context_recall'];
    for (const metric of commonMetrics) {
      if (providers.some(p => p.averageScores[metric] !== undefined)) {
        metricName = metric;
        break;
      }
    }
  }

  // If still no metric, just return alphabetically sorted
  if (!metricName || !providers.some(p => p.averageScores[metricName] !== undefined)) {
    return [...providers].sort((a, b) => a.provider.localeCompare(b.provider));
  }

  // Sort by metric (descending), then by name for ties
  return [...providers].sort((a, b) => {
    const scoreA = a.averageScores[metricName!] ?? -Infinity;
    const scoreB = b.averageScores[metricName!] ?? -Infinity;

    if (scoreB !== scoreA) {
      return scoreB - scoreA;  // Descending
    }
    return a.provider.localeCompare(b.provider);
  });
}

/**
 * Get all unique metric names across all providers
 * Duration-related metrics are sorted to the end
 */
export function getAllMetricNames(providers: ProviderOverallScores[]): string[] {
  const metricsSet = new Set<string>();
  providers.forEach(provider => {
    Object.keys(provider.averageScores).forEach(metric => metricsSet.add(metric));
  });

  const metrics = Array.from(metricsSet);

  // Sort with duration-related metrics at the end
  return metrics.sort((a, b) => {
    const aIsDuration = a.toLowerCase().includes('duration') || a.toLowerCase().includes('seconds');
    const bIsDuration = b.toLowerCase().includes('duration') || b.toLowerCase().includes('seconds');

    if (aIsDuration && !bIsDuration) return 1;  // a goes to end
    if (!aIsDuration && bIsDuration) return -1; // b goes to end

    return a.localeCompare(b); // Otherwise alphabetical
  });
}

/**
 * Format score for display (3 decimal places)
 */
export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined || isNaN(score)) {
    return 'N/A';
  }
  return score.toFixed(3);
}

/**
 * Format duration for display (seconds with 2 decimal places)
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) {
    return 'N/A';
  }
  return `${seconds.toFixed(2)}s`;
}
