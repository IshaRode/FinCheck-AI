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
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk and document metadata.")


class RetrieveResponse(BaseModel):
    question: str = Field(..., description="The queried question.")
    results: List[RetrievedChunk] = Field(..., description="Top relevant retrieved chunks.")
