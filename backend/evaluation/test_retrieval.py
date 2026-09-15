"""
Retrieval Test Script for FinCheck AI.

Tests semantic similarity search against Supabase PostgreSQL + pgvector using halfvec(2048).
Generates query embeddings with NVIDIA NeMo Retriever (nvidia/nemotron-3-embed-1b) using input_type='query'.
Retrieves top 10 chunks using cosine distance.

DO NOT call reranker.
DO NOT call Gemini.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import psycopg2
from psycopg2.extras import RealDictCursor

from backend.app.database import get_db_connection
from backend.app.services.embedding_service import embedding_service


TEST_QUERIES = [
    "What are the RBI rules regarding KYC requirements?",
    "What precautions should customers take to avoid digital arrest scams?",
    "What are the rules related to bank account nominee?",
]


def search_similar_chunks(
    conn, query_embedding: List[float], match_count: int = 10
) -> List[Dict[str, Any]]:
    """
    Executes semantic similarity search using match_document_chunks RPC or direct SQL
    with cosine distance operator (<=>).
    """
    halfvec_str = f"[{','.join(f'{x:.7f}' for x in query_embedding)}]"

    query = """
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
        (dc.embedding <=> %s::halfvec) AS distance,
        (1 - (dc.embedding <=> %s::halfvec)) AS similarity
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE dc.embedding IS NOT NULL
    ORDER BY dc.embedding <=> %s::halfvec
    LIMIT %s;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (halfvec_str, halfvec_str, halfvec_str, match_count))
        return cur.fetchall()


def run_retrieval_tests(queries: List[str] = TEST_QUERIES, top_k: int = 10):
    print("\n==================================================")
    print("PHASE 4: VECTOR RETRIEVAL TEST")
    print("Model: nvidia/nemotron-3-embed-1b (2048 dims, input_type='query')")
    print("Vector Index: HNSW with halfvec_cosine_ops")
    print("==================================================")

    conn = get_db_connection()
    try:
        for q_idx, query_text in enumerate(queries, 1):
            print(f"\n--------------------------------------------------")
            print(f"TEST QUERY #{q_idx}: \"{query_text}\"")
            print(f"--------------------------------------------------")

            # 1. Generate query embedding with input_type = 'query'
            print("[1] Generating query embedding (input_type='query')...")
            query_emb = embedding_service.get_query_embedding(query_text)
            print(f"[2] Received embedding: dimension={len(query_emb)}")

            # 2. Search database
            print(f"[3] Searching top {top_k} nearest chunks in Supabase pgvector...")
            results = search_similar_chunks(conn, query_emb, match_count=top_k)

            print(f"\n[RESULTS] Top {len(results)} chunks retrieved:")
            for rank, r in enumerate(results, 1):
                chunk_id = r["chunk_id"]
                doc_name = r["document_name"]
                source_dataset = r["source_dataset"]
                dist = r["distance"]
                sim = r["similarity"]
                content_preview = r["content"].replace("\n", " ").strip()
                if len(content_preview) > 160:
                    content_preview = content_preview[:160] + "..."

                print(f"\nRank {rank}:")
                print(f"  Chunk ID:        {chunk_id}")
                print(f"  Document Name:   {doc_name}")
                print(f"  Source Dataset:  {source_dataset}")
                print(f"  Cosine Distance: {dist:.4f} (Similarity: {sim:.4f})")
                print(f"  Content Preview: {content_preview}")

    finally:
        conn.close()


if __name__ == "__main__":
    run_retrieval_tests()
