"""
API routes for Grounded Answer Generation with Gemini in FinCheck AI.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from backend.app.models.generation import GenerateRequest, GenerateResponse
from backend.app.services.generation_service import (
    GenerationConfigError,
    GenerationError,
    generation_service,
)
from backend.app.services.retrieval_service import (
    DatabaseError,
    EmbeddingError,
    retrieval_service,
)

logger = logging.getLogger("fincheck.api.generation")

router = APIRouter(prefix="/api/ask", tags=["Generation"])


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a grounded answer for a financial question",
    description=(
        "Executes two-stage retrieval (NVIDIA embeddings + pgvector + NVIDIA reranker) "
        "and generates a strictly grounded answer with source citations using Gemini."
    ),
)
async def generate_answer(request: GenerateRequest) -> GenerateResponse:
    """
    Retrieves the top authoritative document chunks and generates a grounded factual answer.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    # Step 1: Execute Two-Stage Retrieval Pipeline
    try:
        chunks, reranked, total_candidates = retrieval_service.retrieve(
            question=question,
            match_count=request.top_k,
            final_count=request.top_n,
            enable_rerank=request.enable_rerank,
            return_metadata=True,
        )
    except EmbeddingError as e:
        logger.error(f"Embedding service failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The embedding service is temporarily unavailable. Please try again.",
        )
    except DatabaseError as e:
        logger.error(f"Database retrieval failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The knowledge base database is currently unreachable. Please try again.",
        )
    except Exception as e:
        logger.exception(f"Unexpected error during retrieval stage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected retrieval error occurred. Please contact administrator.",
        )

    # Step 2: Generate Grounded Answer via Gemini
    try:
        response = generation_service.generate_answer(
            question=question,
            chunks=chunks,
            temperature=request.temperature,
            total_candidates=total_candidates,
            reranked=reranked,
        )
        return response

    except GenerationConfigError as e:
        logger.warning(f"Generation configuration missing: {e}. Returning fallback response.")
        return generation_service.create_fallback_response(
            question=question,
            chunks=chunks,
            reason="Gemini API key is not configured in the backend environment",
            total_candidates=total_candidates,
            reranked=reranked,
        )

    except GenerationError as e:
        logger.warning(f"Generation service error: {e}. Returning fallback response.")
        return generation_service.create_fallback_response(
            question=question,
            chunks=chunks,
            reason="Gemini generation service timed out or was temporarily unavailable",
            total_candidates=total_candidates,
            reranked=reranked,
        )

    except Exception as e:
        logger.exception(f"Unexpected error during generation stage: {e}")
        return generation_service.create_fallback_response(
            question=question,
            chunks=chunks,
            reason="An unexpected error occurred during answer generation",
            total_candidates=total_candidates,
            reranked=reranked,
        )


@router.post(
    "/answer",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def generate_answer_alias(request: GenerateRequest) -> GenerateResponse:
    """Convenience alias for /api/ask/generate."""
    return await generate_answer(request)
