"""
Database Validation Script for FinCheck AI (Phase 4).

Validates:
- Total documents
- Total chunks
- Chunks with embeddings
- Chunks without embeddings
- Duplicate chunk IDs
- Embedding type & dimension
- Total evaluation questions
- HNSW index status
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.database import get_db_connection


def validate_database() -> dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Total documents
            cur.execute("SELECT COUNT(*) FROM documents;")
            total_docs = cur.fetchone()[0]

            # 2. Total chunks
            cur.execute("SELECT COUNT(*) FROM document_chunks;")
            total_chunks = cur.fetchone()[0]

            # 3. Chunks with embeddings
            cur.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;")
            chunks_with_emb = cur.fetchone()[0]

            # 4. Chunks without embeddings
            cur.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NULL;")
            chunks_without_emb = cur.fetchone()[0]

            # 5. Duplicate chunk IDs
            cur.execute(
                """
                SELECT COUNT(*) FROM (
                    SELECT chunk_id FROM document_chunks GROUP BY chunk_id HAVING COUNT(*) > 1
                ) AS dups;
                """
            )
            duplicate_chunk_ids = cur.fetchone()[0]

            # 6. Embedding column type & dimension
            cur.execute(
                """
                SELECT format_type(atttypid, atttypmod)
                FROM pg_attribute
                WHERE attrelid = 'document_chunks'::regclass AND attname = 'embedding';
                """
            )
            col_type = cur.fetchone()
            emb_type_str = col_type[0] if col_type else "unknown"

            # 7. Total evaluation questions
            cur.execute("SELECT COUNT(*) FROM evaluation_questions;")
            total_eval_questions = cur.fetchone()[0]

            # 8. HNSW Index status
            cur.execute(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'document_chunks' AND indexname LIKE '%hnsw%';
                """
            )
            hnsw_rows = cur.fetchall()
            hnsw_status = "present" if hnsw_rows else "missing"
            hnsw_def = hnsw_rows[0][1] if hnsw_rows else None

            report = {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_emb,
                "chunks_without_embeddings": chunks_without_emb,
                "duplicate_chunk_ids": duplicate_chunk_ids,
                "embedding_type": emb_type_str,
                "embedding_dimension": 2048 if "2048" in emb_type_str else "unknown",
                "total_evaluation_questions": total_eval_questions,
                "hnsw_index_status": hnsw_status,
                "hnsw_index_definition": hnsw_def,
            }
            return report
    finally:
        conn.close()


if __name__ == "__main__":
    rep = validate_database()
    print(json.dumps(rep, indent=2))
