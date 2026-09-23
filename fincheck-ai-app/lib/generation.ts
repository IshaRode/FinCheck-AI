/**
 * Type definitions and client API caller for FinCheck AI Grounded Answer Generation.
 */

import type { RetrievedChunk } from '@/lib/retrieval';

export interface GenerateOptions {
  enable_rerank?: boolean;
  top_k?: number;
  top_n?: number;
  temperature?: number;
}

export interface GenerateResponse {
  question: string;
  answer: string;
  is_grounded: boolean;
  is_insufficient_context: boolean;
  sources: RetrievedChunk[];
  cited_source_ids: number[];
  model: string;
  total_candidates: number;
  reranked: boolean;
}

export interface GenerateApiError {
  detail: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Sends a financial question to the FastAPI answer generation endpoint.
 */
export async function generateAnswer(
  question: string,
  options?: GenerateOptions
): Promise<GenerateResponse> {
  const trimmed = question.trim();
  if (!trimmed) {
    throw new Error('Question cannot be empty.');
  }

  // First try the Next.js proxy route, fallback to direct backend URL
  const endpoints = ['/api/ask/generate', `${BACKEND_URL}/api/ask/generate`];
  let lastError: Error | null = null;

  for (const endpoint of endpoints) {
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: trimmed,
          ...(options?.enable_rerank !== undefined && { enable_rerank: options.enable_rerank }),
          ...(options?.top_k !== undefined && { top_k: options.top_k }),
          ...(options?.top_n !== undefined && { top_n: options.top_n }),
          ...(options?.temperature !== undefined && { temperature: options.temperature }),
        }),
      });

      if (!res.ok) {
        let errorMsg = `Generation failed with status ${res.status}`;
        try {
          const errData = await res.json();
          if (errData && typeof errData.detail === 'string') {
            errorMsg = errData.detail;
          }
        } catch {
          // ignore json parse error
        }
        throw new Error(errorMsg);
      }

      const data: GenerateResponse = await res.json();
      return data;
    } catch (err: unknown) {
      lastError = err instanceof Error ? err : new Error(String(err));
    }
  }

  throw lastError || new Error('Failed to connect to the answer generation service.');
}
