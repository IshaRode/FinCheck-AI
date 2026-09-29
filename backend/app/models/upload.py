"""
Pydantic models for PDF Upload and Ingestion in FinCheck AI.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PDFUploadResponse(BaseModel):
    status: str = Field(..., description="'success' or 'already_exists'")
    document_id: str = Field(..., description="Unique document ID (upload_sha256)")
    document_name: str = Field(..., description="Sanitized document filename")
    total_pages: Optional[int] = Field(None, description="Total pages extracted from PDF")
    total_chunks: int = Field(..., description="Number of text chunks embedded and indexed")
    total_tokens: Optional[int] = Field(None, description="Total tokens embedded across chunks")
    source_dataset: str = Field("uploaded_docs", description="Dataset identifier")
    message: str = Field(..., description="Status summary message")


class UploadedDocumentItem(BaseModel):
    document_id: str
    document_name: str
    document_type: str
    source: str
    source_dataset: str
    created_at: Optional[str] = None
    chunk_count: int


class UploadedDocumentsListResponse(BaseModel):
    total_documents: int
    documents: List[UploadedDocumentItem]


class DeleteDocumentResponse(BaseModel):
    success: bool
    document_id: str
    message: str
