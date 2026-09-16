"""
Semantic retrieval service for FinCheck AI.
Retrieves top matching document chunks from Supabase PostgreSQL + pgvector
using NVIDIA Nemotron query embeddings.
"""

import logging
from typing import Any, Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor

from backend.app.database import get_db_connection
from backend.app.models.retrieval import RetrievedChunk
from backend.app.services.embedding_service import embedding_service

logger = logging.getLogger("fincheck.retrieval")


class RetrievalError(Exception):
    """Base exception for retrieval errors."""
    pass


class EmbeddingError(RetrievalError):
    """Raised when query embedding generation fails."""
    pass


class DatabaseError(RetrievalError):
    """Raised when database query execution fails."""
    pass


class RetrievalService:
    def __init__(self, top_k: int = 10):
        self.top_k = top_k

    def retrieve(self, question: str, match_count: int = 10) -> List[RetrievedChunk]:
        """
        Executes semantic retrieval for a user question:
        1. Generates 2048-dimensional query embedding via NVIDIA API (input_type='query').
        2. Queries Supabase pgvector using match_document_chunks RPC or cosine similarity.
        3. Returns ordered list of RetrievedChunk objects.
        """
        # Step 1: Generate query embedding
        try:
            query_embedding = embedding_service.get_query_embedding(question)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise EmbeddingError("Failed to generate embedding for the query. Please verify NVIDIA API configuration.") from e

        # Step 2: Query Supabase pgvector
        halfvec_str = f"[{','.join(f'{x:.7f}' for x in query_embedding)}]"

        # Call match_document_chunks RPC function
        rpc_query = """
        SELECT
            chunk_id,
            document_id,
            content,
            metadata,
            document_name,
            source,
            source_dataset,
            section,
            page_number,
            similarity
        FROM match_document_chunks(%s::halfvec, %s);
        """

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(rpc_query, (halfvec_str, match_count))
                rows = cur.fetchall()
        except Exception as e:
            logger.error(f"Database retrieval query failed: {e}")
            raise DatabaseError("Failed to retrieve documents from the database. Please check connection.") from e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        # Step 3: Format into domain objects
        results: List[RetrievedChunk] = []
        for idx, row in enumerate(rows, 1):
            raw_meta = row.get("metadata")
            meta = raw_meta if isinstance(raw_meta, dict) else {}

            # Attach section/page_number if present
            if row.get("section") and "section" not in meta:
                meta["section"] = row["section"]
            if row.get("page_number") is not None and "page_number" not in meta:
                meta["page_number"] = row["page_number"]

            sim = float(row.get("similarity", 0.0))
            # Clamp similarity between 0.0 and 1.0
            clamped_sim = max(0.0, min(1.0, round(sim, 4)))

            results.append(
                RetrievedChunk(
                    rank=idx,
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    document_name=str(row.get("document_name") or "Unknown Document"),
                    source=str(row.get("source") or "RBI / Financial Inclusion"),
                    source_dataset=str(row.get("source_dataset") or "corpus"),
                    content=str(row["content"]),
                    similarity=clamped_sim,
                    metadata=meta,
                )
            )

        return results


# Global singleton service instance
retrieval_service = RetrievalService()
