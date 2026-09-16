"""
Corpus and Evaluation Ingestion Script for FinCheck AI.

Ingests:
1. Documents (from data/normalized/combined_corpus.jsonl) into 'documents' table
2. Document Chunks (from data/normalized/chunks.jsonl) into 'document_chunks' table with halfvec(2048) embeddings
3. Evaluation Questions (from data/evaluation/*.jsonl) into 'evaluation_questions' table (WITHOUT embeddings)

Idempotent and resumable:
- Checks existing document_ids and chunk_ids
- Only embeds and inserts chunks that do not exist or lack embeddings
- Multi-threaded batch processing with progress logging and failure tolerance
"""

import concurrent.futures
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import psycopg2
from psycopg2.extras import Json, execute_batch

from backend.app.config import settings
from backend.app.database import apply_migrations, get_db_connection, verify_connection
from backend.app.services.embedding_service import embedding_service


def format_halfvec(embedding: List[float]) -> str:
    """Formats a float array into a PostgreSQL halfvec literal string: '[x1,x2,...]'."""
    return f"[{','.join(f'{x:.7f}' for x in embedding)}]"


def parse_date(date_val: Any) -> Optional[str]:
    """Ensures date is a valid YYYY-MM-DD string or returns None for SQL NULL."""
    if not date_val or not isinstance(date_val, str):
        return None
    date_str = date_val.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str
    return None


def ingest_documents(conn, documents_path: str) -> int:
    """Ingests parent document records into 'documents' table."""
    print(f"\n[STEP 1] Ingesting documents from {documents_path}...")
    if not os.path.exists(documents_path):
        raise FileNotFoundError(f"Documents file not found: {documents_path}")

    docs_to_insert = []
    with open(documents_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                docs_to_insert.append((
                    d["document_id"],
                    d["document_name"],
                    d["document_type"],
                    d["source"],
                    d["source_dataset"],
                    parse_date(d.get("issued_date")),
                    d.get("regulation_area"),
                    d.get("applicable_to"),
                ))

    query = """
    INSERT INTO documents (
        id, document_name, document_type, source, source_dataset,
        issued_date, regulation_area, applicable_to
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        document_name = EXCLUDED.document_name,
        regulation_area = EXCLUDED.regulation_area,
        applicable_to = EXCLUDED.applicable_to;
    """

    with conn.cursor() as cur:
        execute_batch(cur, query, docs_to_insert, page_size=200)
    conn.commit()

    print(f"[SUCCESS] Upserted {len(docs_to_insert)} parent documents.")
    return len(docs_to_insert)


def get_existing_chunk_ids(conn) -> Set[str]:
    """Retrieves all chunk_ids that already exist and have valid embeddings."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT chunk_id FROM document_chunks WHERE embedding IS NOT NULL;"
        )
        rows = cur.fetchall()
        return {r[0] for r in rows}


def process_batch(batch: List[Dict[str, Any]], batch_num: int, total_batches: int) -> Tuple[int, int, int]:
    """
    Worker function to embed a single batch of chunks and insert into PostgreSQL.
    Returns: (embedded_count, inserted_count, failed_count)
    """
    texts = [ch["content"] for ch in batch]
    chunk_ids = [ch["chunk_id"] for ch in batch]

    insert_query = """
    INSERT INTO document_chunks (
        id, document_id, chunk_id, content, chunk_index,
        total_chunks_in_doc, token_count, page_number, section,
        embedding, metadata
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::halfvec, %s)
    ON CONFLICT (chunk_id) DO UPDATE SET
        embedding = EXCLUDED.embedding,
        content = EXCLUDED.content,
        metadata = EXCLUDED.metadata;
    """

    conn = get_db_connection()
    try:
        # NVIDIA NeMo Retriever Embedding in PASSAGE mode
        embeddings = embedding_service.get_embeddings(texts, input_type="passage")

        rows_to_insert = []
        for ch, emb in zip(batch, embeddings):
            meta = ch.get("metadata", {})
            rows_to_insert.append((
                ch["chunk_id"],
                ch["document_id"],
                ch["chunk_id"],
                ch["content"],
                meta.get("chunk_index", 1),
                meta.get("total_chunks_in_doc", 1),
                meta.get("token_count", len(ch["content"].split())),
                ch.get("page_number"),
                ch.get("section"),
                format_halfvec(emb),
                Json(meta),
            ))

        with conn.cursor() as cur:
            execute_batch(cur, insert_query, rows_to_insert, page_size=len(rows_to_insert))
        conn.commit()

        print(f"[Batch {batch_num}/{total_batches}] Successfully ingested {len(rows_to_insert)} chunks.")
        return len(embeddings), len(rows_to_insert), 0

    except Exception as e:
        print(f"[ERROR] Batch {batch_num}/{total_batches} failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return 0, 0, len(batch)
    finally:
        conn.close()


def ingest_chunks(
    conn,
    chunks_path: str,
    batch_size: int = 48,
    max_workers: int = 4,
) -> Dict[str, int]:
    """
    Ingests chunks into document_chunks table with 2048-dimensional halfvec embeddings.
    Uses multi-threaded parallel execution for high throughput.
    Resumable and idempotent.
    """
    print(f"\n[STEP 2] Ingesting document chunks from {chunks_path}...")
    if not os.path.exists(chunks_path):
        raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

    all_chunks = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                all_chunks.append(json.loads(line))

    total_chunks = len(all_chunks)
    existing_chunk_ids = get_existing_chunk_ids(conn)
    existing_count = len(existing_chunk_ids)

    chunks_to_process = [
        ch for ch in all_chunks if ch["chunk_id"] not in existing_chunk_ids
    ]
    new_chunks = len(chunks_to_process)

    print(f"Total chunks in file: {total_chunks}")
    print(f"Already embedded in DB: {existing_count}")
    print(f"New chunks to embed: {new_chunks}")

    if new_chunks == 0:
        print("[INFO] All chunks already embedded and stored in database.")
        return {
            "total_chunks": total_chunks,
            "existing_chunks": existing_count,
            "new_chunks": 0,
            "embedded_successfully": 0,
            "inserted_successfully": 0,
            "failed": 0,
            "skipped": existing_count,
        }

    # Split into batches
    batches = [
        chunks_to_process[i : i + batch_size]
        for i in range(0, new_chunks, batch_size)
    ]
    total_batches = len(batches)
    print(f"Processing {new_chunks} chunks in {total_batches} batches with {max_workers} concurrent workers...")

    embedded_successfully = 0
    inserted_successfully = 0
    failed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {
            executor.submit(process_batch, b, idx + 1, total_batches): idx
            for idx, b in enumerate(batches)
        }

        for future in concurrent.futures.as_completed(future_to_batch):
            emb_c, ins_c, fail_c = future.result()
            embedded_successfully += emb_c
            inserted_successfully += ins_c
            failed += fail_c

    stats = {
        "total_chunks": total_chunks,
        "existing_chunks": existing_count,
        "new_chunks": new_chunks,
        "embedded_successfully": embedded_successfully,
        "inserted_successfully": inserted_successfully,
        "failed": failed,
        "skipped": existing_count,
    }
    return stats


def ingest_evaluation_questions(
    conn, rbi_eval_path: str, fin_eval_path: str
) -> int:
    """
    Ingests evaluation questions into 'evaluation_questions' table.
    NOTE: Evaluation questions are NOT embedded into document_chunks.
    """
    print(f"\n[STEP 3] Ingesting evaluation questions...")
    eval_rows = []

    if os.path.exists(rbi_eval_path):
        with open(rbi_eval_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if line:
                    item = json.loads(line)
                    q_id = f"eval_rbi_{idx+1:05d}"
                    eval_rows.append((
                        q_id,
                        item["question"],
                        item["expected_answer"],
                        item.get("document", "RBI Circular"),
                        "rbi",
                        Json(item.get("metadata", {})),
                    ))

    if os.path.exists(fin_eval_path):
        with open(fin_eval_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if line:
                    item = json.loads(line)
                    q_id = f"eval_fin_{idx+1:05d}"
                    eval_rows.append((
                        q_id,
                        item["question"],
                        item["expected_answer"],
                        "Indian Financial Inclusion Reference",
                        "indian_finance",
                        Json(item.get("metadata", {})),
                    ))

    insert_eval_query = """
    INSERT INTO evaluation_questions (
        id, question, expected_answer, source, dataset_source, metadata
    )
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        expected_answer = EXCLUDED.expected_answer,
        metadata = EXCLUDED.metadata;
    """

    with conn.cursor() as cur:
        execute_batch(cur, insert_eval_query, eval_rows, page_size=200)
    conn.commit()

    print(f"[SUCCESS] Upserted {len(eval_rows)} evaluation questions.")
    return len(eval_rows)


def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    docs_path = str(base_dir / "data" / "normalized" / "combined_corpus.jsonl")
    chunks_path = str(base_dir / "data" / "normalized" / "chunks.jsonl")
    rbi_eval_path = str(base_dir / "data" / "evaluation" / "rbi_eval.jsonl")
    fin_eval_path = str(base_dir / "data" / "evaluation" / "indian_finance_eval.jsonl")

    # 1. Verify Connection and pgvector
    conn_info = verify_connection()
    print("[1/4] Database connection verified:")
    for k, v in conn_info.items():
        print(f"  {k}: {v}")

    # 2. Apply migrations
    apply_migrations()

    conn = get_db_connection()
    try:
        # 3. Ingest documents
        doc_count = ingest_documents(conn, docs_path)

        # 4. Ingest chunks with halfvec(2048) embeddings
        chunk_stats = ingest_chunks(conn, chunks_path, batch_size=48, max_workers=4)

        # 5. Ingest evaluation questions (un-embedded)
        eval_count = ingest_evaluation_questions(conn, rbi_eval_path, fin_eval_path)

        print("\n==================================================")
        print("INGESTION REPORT")
        print("==================================================")
        print(f"Total documents: {doc_count}")
        for k, v in chunk_stats.items():
            print(f"{k}: {v}")
        print(f"Evaluation questions: {eval_count}")
        print("==================================================")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
