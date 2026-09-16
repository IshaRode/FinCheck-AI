/**
 * Type definitions and client API caller for FinCheck AI semantic retrieval.
 */

export interface RetrievedChunk {
  rank: number;
  chunk_id: string;
  document_id: string;
  document_name: string;
  source: string;
  source_dataset: string;
  content: string;
  similarity: number;
  metadata?: Record<string, unknown>;
}

export interface RetrieveResponse {
  question: string;
  results: RetrievedChunk[];
}

export interface RetrievalApiError {
  detail: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Sends question to the FastAPI retrieval endpoint.
 */
export async function retrieveSources(question: string): Promise<RetrieveResponse> {
  const trimmed = question.trim();
  if (!trimmed) {
    throw new Error('Question cannot be empty.');
  }

  // First try the Next.js proxy route, fallback to direct backend URL
  const endpoints = ['/api/ask/retrieve', `${BACKEND_URL}/api/ask/retrieve`];
  let lastError: Error | null = null;

  for (const endpoint of endpoints) {
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!res.ok) {
        let errorMsg = `Retrieval failed with status ${res.status}`;
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

      const data: RetrieveResponse = await res.json();
      return data;
    } catch (err: unknown) {
      lastError = err instanceof Error ? err : new Error(String(err));
      // If relative URL failed (e.g. rewrite not handling it), try direct URL next
    }
  }

  throw lastError || new Error('Failed to connect to the retrieval service.');
}
