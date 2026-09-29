"""
API Router for PDF Document Upload & Ingestion in FinCheck AI.
Endpoints:
- POST /api/upload/pdf: Upload and automatically ingest a financial PDF into pgvector.
- GET /api/upload/documents: List all user-uploaded documents in the knowledge base.
- DELETE /api/upload/documents/{document_id}: Remove an uploaded document from the corpus.
"""

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.models.upload import (
    DeleteDocumentResponse,
    PDFUploadResponse,
    UploadedDocumentsListResponse,
)
from backend.app.services.pdf_ingestion_service import (
    PDFExtractionError,
    PDFIngestionError,
    PDFValidationError,
    pdf_ingestion_service,
)

logger = logging.getLogger("fincheck.api.upload")

router = APIRouter(prefix="/api/upload", tags=["Upload & Ingestion"])


@router.post(
    "/pdf",
    response_model=PDFUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and ingest a financial PDF document",
    description=(
        "Uploads a PDF document, extracts text page-by-page, chunks it into semantic units, "
        "generates 2048-dim NVIDIA NeMo embeddings, and stores them in Supabase pgvector."
    ),
)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF document file to ingest"),
) -> PDFUploadResponse:
    """
    Validates, parses, chunks, embeds, and indexes a PDF document into FinCheck AI.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF (.pdf) documents are accepted for knowledge base ingestion.",
        )

    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file data.",
        )

    try:
        result = pdf_ingestion_service.process_and_ingest_pdf(
            file_bytes=file_bytes,
            filename=file.filename,
        )
        return PDFUploadResponse(**result)

    except PDFValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PDFExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except PDFIngestionError as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document indexing failed: {e}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during PDF ingestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the PDF.",
        )


@router.get(
    "/documents",
    response_model=UploadedDocumentsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List uploaded documents",
    description="Retrieves all documents uploaded via the ingestion pipeline.",
)
async def list_uploaded_documents() -> UploadedDocumentsListResponse:
    try:
        docs = pdf_ingestion_service.list_uploaded_documents()
        return UploadedDocumentsListResponse(
            total_documents=len(docs),
            documents=docs,
        )
    except Exception as e:
        logger.error(f"Failed to fetch uploaded documents list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve uploaded documents.",
        )


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an uploaded document",
    description="Deletes an uploaded document and removes its indexed chunks from pgvector.",
)
async def delete_uploaded_document(document_id: str) -> DeleteDocumentResponse:
    try:
        deleted = pdf_ingestion_service.delete_uploaded_document(document_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found or cannot be deleted.",
            )
        return DeleteDocumentResponse(
            success=True,
            document_id=document_id,
            message=f"Document '{document_id}' and all associated chunks were successfully deleted.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete uploaded document.",
        )
