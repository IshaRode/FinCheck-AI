"""
API routes for document chunk retrieval in FinCheck AI.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from backend.app.models.retrieval import RetrieveRequest, RetrieveResponse
from backend.app.services.retrieval_service import (
    DatabaseError,
    EmbeddingError,
    retrieval_service,
)

logger = logging.getLogger("fincheck.api.retrieval")

router = APIRouter(prefix="/api/ask", tags=["Retrieval"])


@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve top relevant banking document chunks for a question",
    description="Generates query embedding via NVIDIA Nemotron and retrieves top 10 chunks from Supabase pgvector.",
)
async def retrieve_chunks(request: RetrieveRequest) -> RetrieveResponse:
    """
    Retrieves the top 10 most relevant chunks matching the user's question.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    try:
        results, reranked, total_candidates = retrieval_service.retrieve(
            question=question,
            match_count=request.top_k,
            final_count=request.top_n,
            enable_rerank=request.enable_rerank,
            return_metadata=True,
        )
        return RetrieveResponse(
            question=question,
            results=results,
            reranked=reranked,
            total_candidates=total_candidates,
        )

    except EmbeddingError as e:
        logger.error(f"Embedding service failure for query: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The embedding service is temporarily unavailable. Please try again.",
        )

    except DatabaseError as e:
        logger.error(f"Database query failure for query: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The knowledge base database is currently unreachable. Please try again.",
        )

    except Exception as e:
        logger.exception(f"Unexpected error during retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request.",
        )
