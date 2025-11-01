'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  calculateOverallScores,
  sortProvidersByMetric,
  getAllMetricNames,
  formatScore,
  formatDuration,
  type ProviderOverallScores,
} from '@/lib/aggregateScores';
import type { DocumentResult } from '@/types/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { AxisDomain } from 'recharts/types/util/types';
import { TrendingUp } from 'lucide-react';

interface OverallResultsCardProps {
  documents: DocumentResult[];
  providers: string[];
}

export function OverallResultsCard({ documents, providers }: OverallResultsCardProps) {
  // Calculate overall scores
  const overallScores = calculateOverallScores(documents, providers);
  const sortedScores = sortProvidersByMetric(overallScores);
  const metricNames = getAllMetricNames(sortedScores);

  // State for selected metric in chart
  const primaryMetric = findPrimaryMetric(sortedScores);
  const [selectedMetric, setSelectedMetric] = useState<string>(primaryMetric);

  // Prepare chart data for selected metric
  const chartData = sortedScores.map(p => ({
    provider: p.provider,
    score: p.averageScores[selectedMetric] ?? 0,
  }));

  // Determine if the selected metric is duration-based (needs different Y-axis scale)
  const isDurationMetric = selectedMetric.toLowerCase().includes('duration') ||
                          selectedMetric.toLowerCase().includes('seconds');

  // Calculate appropriate Y-axis domain
  const yAxisDomain: AxisDomain = isDurationMetric
    ? ([0, 'auto'] as const)  // Auto-scale for duration (can be 100s of seconds)
    : ([0, 1] as const);      // Fixed 0-1 for score metrics

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          <CardTitle>Overall Results</CardTitle>
        </div>
        <CardDescription>
          Aggregated scores across all {documents.length} document{documents.length !== 1 ? 's' : ''}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Scores Table */}
          <div>
            <h4 className="text-sm font-medium mb-3">Average Scores by Provider</h4>
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-3 py-2 text-left font-medium">Provider</th>
                    <th className="px-3 py-2 text-left font-medium">Avg Duration</th>
                    <th className="px-3 py-2 text-left font-medium">Success</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedScores.map((result) => (
                    <tr key={result.provider} className="border-b last:border-0">
                      <td className="px-3 py-2">
                        <span className="font-medium">{result.provider}</span>
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {formatDuration(result.averageDuration)}
                      </td>
                      <td className="px-3 py-2">
                        <Badge
                          variant={result.successRate === 1 ? 'default' : result.successRate > 0 ? 'secondary' : 'destructive'}
                          className="text-xs"
                        >
                          {(result.successRate * 100).toFixed(0)}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Metrics Table */}
            <div className="mt-4">
              <h4 className="text-sm font-medium mb-3">Average Metrics</h4>
              <div className="rounded-md border overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="px-3 py-2 text-left font-medium sticky left-0 bg-muted/50">Provider</th>
                      {metricNames.map(metric => (
                        <th key={metric} className="px-3 py-2 text-left font-medium whitespace-nowrap">
                          {formatMetricName(metric)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sortedScores.map(result => (
                      <tr key={result.provider} className="border-b last:border-0">
                        <td className="px-3 py-2 font-medium sticky left-0 bg-background">
                          {result.provider}
                        </td>
                        {metricNames.map(metric => (
                          <td key={metric} className="px-3 py-2 text-muted-foreground tabular-nums">
                            {formatScore(result.averageScores[metric])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right: Chart */}
          <div>
            <h4 className="text-sm font-medium mb-3">
              {formatMetricName(selectedMetric)} Comparison
            </h4>
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="provider"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    domain={yAxisDomain}
                    tick={{ fontSize: 12 }}
                    label={{
                      value: isDurationMetric ? 'Seconds' : 'Score',
                      angle: -90,
                      position: 'insideLeft'
                    }}
                  />
                  <Tooltip
                    formatter={(value: number) => {
                      if (isDurationMetric) {
                        return `${value.toFixed(2)}s`;
                      }
                      return value.toFixed(3);
                    }}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px',
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Bar
                    dataKey="score"
                    fill="hsl(var(--primary))"
                    name={formatMetricName(selectedMetric)}
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Metric Selection Buttons */}
            <div className="mt-4">
              <p className="text-xs text-muted-foreground mb-2">Select metric to compare:</p>
              <div className="flex flex-wrap gap-2">
                {metricNames.map(metric => (
                  <Button
                    key={metric}
                    size="sm"
                    variant={selectedMetric === metric ? 'default' : 'outline'}
                    onClick={() => setSelectedMetric(metric)}
                    className="text-xs"
                  >
                    {formatMetricName(metric)}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Find the primary metric to use for chart visualization
 * Prefers factual_correctness, then faithfulness, then first available
 */
function findPrimaryMetric(scores: ProviderOverallScores[]): string {
  if (scores.length === 0) return '';

  const preferredMetrics = ['factual_correctness(mode=f1)', 'faithfulness', 'context_recall'];

  for (const metric of preferredMetrics) {
    if (scores.some(p => p.averageScores[metric] !== undefined)) {
      return metric;
    }
  }

  // Fallback to first available metric
  const firstProvider = scores[0];
  const metrics = Object.keys(firstProvider.averageScores);
  return metrics[0] || '';
}

/**
 * Format metric name for display (shorten common patterns)
 */
function formatMetricName(metric: string): string {
  // Remove (mode=f1) suffix for brevity
  const cleaned = metric.replace(/\(mode=[^)]+\)/g, '');

  // Convert snake_case to Title Case
  return cleaned
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
