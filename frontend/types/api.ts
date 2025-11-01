/**
 * TypeScript types matching the FastAPI backend response models
 * Based on backend/api/models/responses.py
 */

export interface RunSummary {
  run_id: string;
  dataset: string;
  split: string;
  providers: string[];
  status: 'queued' | 'running' | 'completed' | 'failed';
  num_docs: number;
  num_questions: number;
  started_at: string;  // ISO datetime string
  completed_at: string | null;
  duration_seconds: number | null;
}

export interface QuestionResult {
  question_id: string;
  question: string;
  ground_truth: string;
  response_answer: string;
  response_context: string[];  // Retrieved text chunks
  response_latency_ms: number | null;
  evaluation_scores: Record<string, any>;  // {metric: score}
}

export interface ProviderResult {
  provider: string;
  status: 'success' | 'error';
  error: string | null;
  aggregated_scores: Record<string, any>;  // {metric: avg_score}
  duration_seconds: number | null;
  questions: QuestionResult[];
}

export interface DocumentResult {
  doc_id: string;
  doc_title: string;
  providers: Record<string, ProviderResult>;  // provider_name -> result
}

export interface RunDetail {
  run_id: string;
  dataset: string;
  split: string;
  providers: string[];
  status: 'queued' | 'running' | 'completed' | 'failed';
  num_docs: number;
  num_questions: number;
  config: Record<string, any>;  // Full benchmark config
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  error_message: string | null;
  documents: DocumentResult[];
}

export interface DatasetInfo {
  name: string;
  display_name: string;
  description: string;
  available_splits: string[];
  num_documents: number | null;
  task_type: string;
}

export interface ResultsListResponse {
  runs: RunSummary[];
  total: number;
  limit: number;
  offset: number;
}

// API Error Response
export interface ApiError {
  detail: string;
}
