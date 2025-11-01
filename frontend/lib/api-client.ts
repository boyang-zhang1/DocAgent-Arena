/**
 * API client for RAGRace backend
 */

import type {
  RunSummary,
  RunDetail,
  DatasetInfo,
  ResultsListResponse,
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchWithError<T>(url: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        throw new Error(error.detail || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unknown error occurred');
    }
  }

  /**
   * Get list of benchmark runs with pagination and filtering
   */
  async getResults(params?: {
    dataset?: string;
    limit?: number;
    offset?: number;
  }): Promise<ResultsListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.dataset) searchParams.append('dataset', params.dataset);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    const query = searchParams.toString();
    const url = `/api/v1/results${query ? `?${query}` : ''}`;

    return this.fetchWithError<ResultsListResponse>(url);
  }

  /**
   * Get detailed results for a specific run
   */
  async getRunDetail(runId: string): Promise<RunDetail> {
    return this.fetchWithError<RunDetail>(`/api/v1/results/${runId}`);
  }

  /**
   * Get list of available datasets
   */
  async getDatasets(): Promise<DatasetInfo[]> {
    return this.fetchWithError<DatasetInfo[]>('/api/v1/datasets');
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.fetchWithError('/api/health');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Also export the class for testing
export default ApiClient;
