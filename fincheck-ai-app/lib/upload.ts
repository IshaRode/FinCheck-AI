/**
 * Client helper functions for FinCheck AI PDF Upload & Knowledge Base Ingestion.
 */

export interface PDFUploadResult {
  status: 'success' | 'already_exists';
  document_id: string;
  document_name: string;
  total_pages?: number;
  total_chunks: number;
  total_tokens?: number;
  source_dataset: string;
  message: string;
}

export interface UploadedDocItem {
  document_id: string;
  document_name: string;
  document_type: string;
  source: string;
  source_dataset: string;
  created_at: string | null;
  chunk_count: number;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Uploads a financial PDF to the FastAPI ingestion service.
 */
export async function uploadPdfDocument(file: File): Promise<PDFUploadResult> {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    throw new Error('Only PDF (.pdf) files are supported.');
  }

  const formData = new FormData();
  formData.append('file', file);

  const endpoint = `${BACKEND_URL}/api/upload/pdf`;

  const res = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    let errorDetail = `Upload failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson?.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // Fallback to text
      const errText = await res.text();
      if (errText) errorDetail = errText;
    }
    throw new Error(errorDetail);
  }

  return (await res.json()) as PDFUploadResult;
}

/**
 * Fetches the list of all documents uploaded by users into pgvector.
 */
export async function fetchUploadedDocuments(): Promise<UploadedDocItem[]> {
  const endpoint = `${BACKEND_URL}/api/upload/documents`;
  try {
    const res = await fetch(endpoint, {
      method: 'GET',
    });
    if (!res.ok) {
      return [];
    }
    const data = await res.json();
    return data.documents || [];
  } catch {
    return [];
  }
}

/**
 * Deletes an uploaded document and its indexed chunks.
 */
export async function deleteUploadedDocument(documentId: string): Promise<boolean> {
  const endpoint = `${BACKEND_URL}/api/upload/documents/${encodeURIComponent(documentId)}`;
  const res = await fetch(endpoint, {
    method: 'DELETE',
  });
  return res.ok;
}
