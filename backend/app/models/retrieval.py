"""
Pydantic models for semantic retrieval API requests and responses.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class RetrieveRequest(BaseModel):
    question: str = Field(
        ...,
        description="The user's financial question to search across banking documents.",
        examples=["What are the RBI rules regarding KYC requirements?"],
    )
    enable_rerank: bool = Field(
        default=True,
        description="Whether to apply NVIDIA cross-encoder reranking to initial vector candidates.",
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Number of candidate chunks to retrieve from vector search (default 15).",
        ge=1,
        le=50,
    )
    top_n: Optional[int] = Field(
        default=None,
        description="Number of final chunks to return after reranking (default 5).",
        ge=1,
        le=20,
    )

    @field_validator("question", mode="before")
    @classmethod
    def validate_question(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Question must be a string.")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Question cannot be empty or whitespace only.")
        if len(trimmed) < 3:
            raise ValueError("Question must be at least 3 characters long.")
        if len(trimmed) > 1000:
            raise ValueError("Question is too long (maximum 1000 characters).")
        return trimmed


class RetrievedChunk(BaseModel):
    rank: int = Field(..., description="1-based relevance rank.")
    chunk_id: str = Field(..., description="Unique chunk identifier.")
    document_id: str = Field(..., description="Parent document identifier.")
    document_name: str = Field(..., description="Document title or circular name.")
    source: str = Field(..., description="Source agency or publication.")
    source_dataset: str = Field(..., description="Dataset origin: 'rbi' or 'indian_finance'.")
    content: str = Field(..., description="Retrieved passage content.")
    similarity: float = Field(..., description="Cosine similarity score (0.0 to 1.0).")
    rerank_score: Optional[float] = Field(default=None, description="NVIDIA Reranker sigmoid probability score (0.0 to 1.0).")
    rerank_logit: Optional[float] = Field(default=None, description="NVIDIA Reranker raw logit score.")
    initial_rank: Optional[int] = Field(default=None, description="Original 1-based rank from vector retrieval before reranking.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk and document metadata.")


class RetrieveResponse(BaseModel):
    question: str = Field(..., description="The queried question.")
    results: List[RetrievedChunk] = Field(..., description="Top relevant retrieved chunks.")
    reranked: bool = Field(default=False, description="Whether reranking was successfully applied.")
    total_candidates: int = Field(default=0, description="Total vector candidates evaluated.")

