"""
Semantic retrieval service for FinCheck AI.
Retrieves top matching document chunks from Supabase PostgreSQL + pgvector
using NVIDIA Nemotron query embeddings (2048-dim), then applies NVIDIA
cross-encoder reranking (nvidia/llama-nemotron-rerank-vl-1b-v2) for precision.
Includes graceful fallback to vector similarity if reranking encounters transient errors.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

from backend.app.config import settings
from backend.app.database import get_db_connection
from backend.app.models.retrieval import RetrievedChunk
from backend.app.services.embedding_service import embedding_service
from backend.app.services.reranking_service import reranking_service

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
    def __init__(
        self,
        top_k: Optional[int] = None,
        final_top_n: Optional[int] = None,
    ):
        self.top_k = top_k or settings.RETRIEVAL_TOP_K
        self.final_top_n = final_top_n or settings.FINAL_RERANK_TOP_N

    def retrieve(
        self,
        question: str,
        match_count: Optional[int] = None,
        final_count: Optional[int] = None,
        enable_rerank: Optional[bool] = None,
        return_metadata: bool = False,
    ) -> Any:
        """
        Executes semantic retrieval with optional cross-encoder reranking:
        1. Generates 2048-dim query embedding via NVIDIA API (input_type='query').
        2. Retrieves Top K candidates from Supabase pgvector using match_document_chunks.
        3. If enable_rerank is True, reranks candidates using NVIDIA cross-encoder.
           - On success: Returns top N reranked chunks with both similarity and rerank_score.
           - On failure/timeout: Falls back gracefully to top N vector similarity chunks.
        4. If return_metadata is True, returns (results, is_reranked, total_candidates).
           Otherwise, returns results (List[RetrievedChunk]).
        """
        k = match_count if match_count is not None else self.top_k
        n = final_count if final_count is not None else self.final_top_n
        should_rerank = (
            settings.RERANK_ENABLED if enable_rerank is None else enable_rerank
        )

        # Step 1: Generate query embedding
        try:
            query_embedding = embedding_service.get_query_embedding(question)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise EmbeddingError(
                "Failed to generate embedding for the query. Please verify NVIDIA API configuration."
            ) from e

        # Step 2: Query Supabase pgvector for top K candidates
        halfvec_str = f"[{','.join(f'{x:.7f}' for x in query_embedding)}]"

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
                cur.execute(rpc_query, (halfvec_str, k))
                rows = cur.fetchall()
        except Exception as e:
            logger.error(f"Database retrieval query failed: {e}")
            raise DatabaseError(
                "Failed to retrieve documents from the database. Please check connection."
            ) from e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        # Step 3: Format initial vector candidates
        candidates: List[RetrievedChunk] = []
        for idx, row in enumerate(rows, 1):
            raw_meta = row.get("metadata")
            meta = raw_meta if isinstance(raw_meta, dict) else {}

            if row.get("section") and "section" not in meta:
                meta["section"] = row["section"]
            if row.get("page_number") is not None and "page_number" not in meta:
                meta["page_number"] = row["page_number"]

            sim = float(row.get("similarity", 0.0))
            clamped_sim = max(0.0, min(1.0, round(sim, 4)))

            candidates.append(
                RetrievedChunk(
                    rank=idx,
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    document_name=str(row.get("document_name") or "Unknown Document"),
                    source=str(row.get("source") or "RBI / Financial Inclusion"),
                    source_dataset=str(row.get("source_dataset") or "corpus"),
                    content=str(row["content"]),
                    similarity=clamped_sim,
                    rerank_score=None,
                    rerank_logit=None,
                    initial_rank=idx,
                    metadata=meta,
                )
            )

        total_candidates = len(candidates)
        if total_candidates == 0:
            if return_metadata:
                return [], False, 0
            return []

        # Step 4: Cross-Encoder Reranking
        is_reranked = False
        final_results: List[RetrievedChunk] = []

        if should_rerank:
            try:
                passages = [c.content for c in candidates]
                logger.info(
                    f"Reranking {len(passages)} candidates for query: '{question[:60]}...'"
                )
                rankings = reranking_service.rerank(question, passages)

                if rankings:
                    for rerank_rank, item in enumerate(rankings[:n], 1):
                        orig_idx = item["index"]
                        if 0 <= orig_idx < len(candidates):
                            cand = candidates[orig_idx]
                            final_results.append(
                                RetrievedChunk(
                                    rank=rerank_rank,
                                    chunk_id=cand.chunk_id,
                                    document_id=cand.document_id,
                                    document_name=cand.document_name,
                                    source=cand.source,
                                    source_dataset=cand.source_dataset,
                                    content=cand.content,
                                    similarity=cand.similarity,
                                    rerank_score=item["score"],
                                    rerank_logit=item["logit"],
                                    initial_rank=cand.initial_rank,
                                    metadata=cand.metadata,
                                )
                            )
                    is_reranked = True
                    logger.info(
                        f"Successfully reranked into top {len(final_results)} chunks."
                    )
                else:
                    logger.warning("Reranker returned empty rankings. Falling back to vector order.")
                    final_results = candidates[:n]

            except Exception as e:
                logger.warning(
                    f"Reranker error or timeout ({e}). Gracefully falling back to top {n} vector similarity chunks."
                )
                final_results = candidates[:n]
                is_reranked = False
        else:
            final_results = candidates[:n]
            is_reranked = False

        if return_metadata:
            return final_results, is_reranked, total_candidates
        return final_results


# Global singleton service instance
retrieval_service = RetrievalService()
