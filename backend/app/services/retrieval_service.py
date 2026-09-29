"""
Hybrid retrieval service for FinCheck AI (Phase 7B).
Combines:
1. Semantic vector search from Supabase pgvector using NVIDIA Nemotron query embeddings (2048-dim).
2. PostgreSQL keyword/full-text search for exact circular codes, policy names, regulation terms, and phrases.
3. Reciprocal Rank Fusion (RRF) and deduplication across candidate streams.
4. NVIDIA cross-encoder reranking (nvidia/llama-nemotron-rerank-vl-1b-v2) for precision scoring.
5. Graceful fallback on network/reranker failure.
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
        search_mode: Optional[str] = None,
    ):
        self.top_k = top_k or settings.RETRIEVAL_TOP_K
        self.final_top_n = final_top_n or settings.FINAL_RERANK_TOP_N
        self.search_mode = search_mode or getattr(settings, "SEARCH_MODE", "hybrid")

    def vector_search(
        self,
        query_embedding: List[float],
        match_count: int,
    ) -> List[RetrievedChunk]:
        """
        Retrieves top K candidates using Supabase pgvector cosine similarity.
        """
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
                cur.execute(rpc_query, (halfvec_str, match_count))
                rows = cur.fetchall()
        except Exception as e:
            logger.error(f"Vector search query failed: {e}")
            raise DatabaseError("Failed to retrieve documents via vector search.") from e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

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
                    keyword_score=None,
                    retrieval_source="vector",
                    rerank_score=None,
                    rerank_logit=None,
                    initial_rank=idx,
                    metadata=meta,
                )
            )
        return candidates

    def keyword_search(
        self,
        question: str,
        match_count: int,
    ) -> List[RetrievedChunk]:
        """
        Retrieves top K candidates using PostgreSQL full-text search with exact phrase matching.
        """
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Primary: keyword_search_document_chunks RPC function
                try:
                    cur.execute(
                        "SELECT * FROM keyword_search_document_chunks(%s, %s);",
                        (question, match_count),
                    )
                    rows = cur.fetchall()
                except Exception:
                    # Fallback direct query if RPC is not present
                    conn.rollback()
                    fallback_sql = """
                    SELECT
                        dc.chunk_id,
                        dc.document_id,
                        dc.content,
                        dc.metadata,
                        d.document_name,
                        d.source,
                        d.source_dataset,
                        dc.section,
                        dc.page_number,
                        COALESCE(ts_rank(to_tsvector('english', dc.content), plainto_tsquery('english', %s)), 0.0)::FLOAT as keyword_score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE to_tsvector('english', dc.content) @@ plainto_tsquery('english', %s)
                       OR dc.content ILIKE %s
                       OR d.document_name ILIKE %s
                    ORDER BY keyword_score DESC
                    LIMIT %s;
                    """
                    like_pat = f"%{question[:100]}%"
                    cur.execute(fallback_sql, (question, question, like_pat, like_pat, match_count))
                    rows = cur.fetchall()
        except Exception as e:
            logger.error(f"Keyword search query failed: {e}")
            raise DatabaseError("Failed to retrieve documents via keyword search.") from e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        candidates: List[RetrievedChunk] = []
        for idx, row in enumerate(rows, 1):
            raw_meta = row.get("metadata")
            meta = raw_meta if isinstance(raw_meta, dict) else {}
            if row.get("section") and "section" not in meta:
                meta["section"] = row["section"]
            if row.get("page_number") is not None and "page_number" not in meta:
                meta["page_number"] = row["page_number"]

            kw_score = float(row.get("keyword_score", 0.0))
            # Normalized proxy similarity for keyword candidates (0.40 - 0.95 range)
            norm_sim = min(0.95, max(0.40, round(kw_score / (kw_score + 1.0), 4)))

            candidates.append(
                RetrievedChunk(
                    rank=idx,
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    document_name=str(row.get("document_name") or "Unknown Document"),
                    source=str(row.get("source") or "RBI / Financial Inclusion"),
                    source_dataset=str(row.get("source_dataset") or "corpus"),
                    content=str(row["content"]),
                    similarity=norm_sim,
                    keyword_score=round(kw_score, 4),
                    retrieval_source="keyword",
                    rerank_score=None,
                    rerank_logit=None,
                    initial_rank=idx,
                    metadata=meta,
                )
            )
        return candidates

    def hybrid_search(
        self,
        question: str,
        query_embedding: List[float],
        vector_k: int,
        keyword_k: int,
    ) -> List[RetrievedChunk]:
        """
        Executes parallel vector and keyword retrieval, merging and deduplicating
        via Reciprocal Rank Fusion (RRF: 1 / (60 + rank)).
        """
        vector_candidates = self.vector_search(query_embedding, vector_k)
        keyword_candidates = self.keyword_search(question, keyword_k)

        rrf_scores: Dict[str, float] = {}
        unified_chunks: Dict[str, RetrievedChunk] = {}
        rrf_k = 60.0

        # Process vector stream
        for r_v, chunk in enumerate(vector_candidates, 1):
            cid = chunk.chunk_id
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + r_v))
            chunk.metadata["vector_rank"] = r_v
            chunk.metadata["retrieval_source"] = "vector"
            unified_chunks[cid] = chunk

        # Process keyword stream & deduplicate
        for r_k, chunk in enumerate(keyword_candidates, 1):
            cid = chunk.chunk_id
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + r_k))
            if cid in unified_chunks:
                existing = unified_chunks[cid]
                existing.keyword_score = chunk.keyword_score
                existing.retrieval_source = "both"
                existing.metadata["keyword_rank"] = r_k
                existing.metadata["retrieval_source"] = "both"
                existing.metadata["keyword_score"] = chunk.keyword_score
            else:
                chunk.metadata["keyword_rank"] = r_k
                chunk.metadata["retrieval_source"] = "keyword"
                unified_chunks[cid] = chunk

        # Sort merged candidates by RRF score descending
        sorted_cids = sorted(unified_chunks.keys(), key=lambda c: rrf_scores[c], reverse=True)

        merged_candidates: List[RetrievedChunk] = []
        for idx, cid in enumerate(sorted_cids, 1):
            c = unified_chunks[cid]
            c.initial_rank = idx
            c.rank = idx
            c.metadata["rrf_score"] = round(rrf_scores[cid], 6)
            merged_candidates.append(c)

        logger.info(
            f"Hybrid search merged {len(vector_candidates)} vector and {len(keyword_candidates)} keyword candidates into {len(merged_candidates)} unique chunks."
        )
        return merged_candidates

    def retrieve(
        self,
        question: str,
        match_count: Optional[int] = None,
        final_count: Optional[int] = None,
        enable_rerank: Optional[bool] = None,
        search_mode: Optional[str] = None,
        vector_k: Optional[int] = None,
        keyword_k: Optional[int] = None,
        return_metadata: bool = False,
    ) -> Any:
        """
        Executes unified retrieval pipeline:
        1. Selects search mode: 'hybrid' (default), 'vector', or 'keyword'.
        2. Retrieves candidate chunks from vector, keyword, or hybrid RRF fusion.
        3. Applies NVIDIA cross-encoder reranking over unique candidates.
        4. Returns top N chunks with full metadata and score attribution.
        """
        mode = search_mode or self.search_mode or "hybrid"
        mode = mode.lower()
        if mode not in ("hybrid", "vector", "keyword"):
            mode = "hybrid"

        k = match_count if match_count is not None else self.top_k
        n = final_count if final_count is not None else self.final_top_n
        vk = vector_k or k
        kk = keyword_k or k
        should_rerank = (
            settings.RERANK_ENABLED if enable_rerank is None else enable_rerank
        )

        candidates: List[RetrievedChunk] = []

        if mode == "vector":
            try:
                query_embedding = embedding_service.get_query_embedding(question)
            except Exception as e:
                logger.error(f"Failed to generate query embedding: {e}")
                raise EmbeddingError("Failed to generate embedding for query.") from e
            candidates = self.vector_search(query_embedding, vk)

        elif mode == "keyword":
            candidates = self.keyword_search(question, kk)

        else:  # hybrid
            try:
                query_embedding = embedding_service.get_query_embedding(question)
                candidates = self.hybrid_search(
                    question=question,
                    query_embedding=query_embedding,
                    vector_k=vk,
                    keyword_k=kk,
                )
            except EmbeddingError:
                raise
            except Exception as e:
                logger.warning(f"Hybrid retrieval embedding failed ({e}), falling back to keyword search.")
                candidates = self.keyword_search(question, kk)

        total_candidates = len(candidates)
        if total_candidates == 0:
            if return_metadata:
                return [], False, 0
            return []

        # Cross-Encoder Reranking
        is_reranked = False
        final_results: List[RetrievedChunk] = []

        if should_rerank:
            try:
                passages = [c.content for c in candidates]
                logger.info(
                    f"Reranking {len(passages)} {mode} candidates for query: '{question[:60]}...'"
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
                                    keyword_score=cand.keyword_score,
                                    retrieval_source=cand.retrieval_source,
                                    rerank_score=item["score"],
                                    rerank_logit=item["logit"],
                                    initial_rank=cand.initial_rank,
                                    metadata=cand.metadata,
                                )
                            )
                    is_reranked = True
                    logger.info(
                        f"Successfully reranked into top {len(final_results)} chunks via cross-encoder."
                    )
                else:
                    logger.warning("Reranker returned empty rankings. Falling back to candidate order.")
                    final_results = candidates[:n]

            except Exception as e:
                logger.warning(
                    f"Reranker error or timeout ({e}). Gracefully falling back to top {n} candidates."
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
