"""
PDF Ingestion Service for FinCheck AI (Phase 7A).
Handles:
1. Secure file validation (type, size, magic bytes).
2. Clean text extraction using PyMuPDF (pymupdf).
3. Token-aware text chunking with page and section preservation.
4. NVIDIA NeMo Retriever (2048-dim) passage embeddings.
5. Idempotent storage in Supabase PostgreSQL (documents + document_chunks with halfvec).
6. Safe transaction rollback on failure and duplicate file detection.
"""

import hashlib
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import Json, execute_batch
import tiktoken
import pymupdf

from backend.app.config import settings
from backend.app.database import get_db_connection
from backend.app.services.embedding_service import embedding_service

logger = logging.getLogger("fincheck.pdf_ingestion")

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
MIN_FILE_SIZE_BYTES = 100               # Minimal valid PDF size
TARGET_CHUNK_TOKENS = 550
CHUNK_OVERLAP_TOKENS = 75
MAX_CHUNK_TOKENS = 800


class PDFValidationError(Exception):
    """Raised when PDF file validation fails."""
    pass


class PDFExtractionError(Exception):
    """Raised when text extraction from PDF fails."""
    pass


class PDFIngestionError(Exception):
    """Raised when embedding or database persistence fails."""
    pass


def get_tokenizer():
    """Returns tiktoken cl100k_base tokenizer."""
    return tiktoken.get_encoding("cl100k_base")


def sanitize_filename(filename: str) -> str:
    """Sanitizes filename removing directory traversal characters and invalid symbols."""
    base = os.path.basename(filename).strip()
    # Replace unsafe characters
    clean = re.sub(r"[^\w\s\.-]", "_", base)
    # Collapse whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean.lower().endswith(".pdf"):
        clean += ".pdf"
    return clean[:250]


def validate_pdf_bytes(file_bytes: bytes, filename: str) -> None:
    """
    Validates PDF file integrity, size, extension, and magic header.
    """
    if not filename or not filename.lower().endswith(".pdf"):
        raise PDFValidationError("Invalid file extension. Only .pdf files are accepted.")

    size = len(file_bytes)
    if size < MIN_FILE_SIZE_BYTES:
        raise PDFValidationError("File is empty or too small to be a valid PDF.")

    if size > MAX_FILE_SIZE_BYTES:
        raise PDFValidationError(
            f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # Magic bytes check: PDF specification starts with %PDF-
    if not file_bytes.startswith(b"%PDF-"):
        raise PDFValidationError("File header does not match valid PDF format (missing %PDF- magic bytes).")


def extract_text_from_pdf(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Extracts structured text page-by-page from PDF bytes using PyMuPDF.
    Returns a list of page dicts: [{'page_number': int, 'text': str}].
    """
    pages: List[Dict[str, Any]] = []
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise PDFExtractionError(f"Corrupt or unreadable PDF document: {e}") from e

    try:
        if len(doc) == 0:
            raise PDFExtractionError("PDF contains no pages.")

        for idx in range(len(doc)):
            page = doc[idx]
            page_text = page.get_text("text") or ""
            # Clean up excessive repeated whitespace / line breaks
            cleaned = re.sub(r"\r\n|\r", "\n", page_text)
            cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
            cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()

            if cleaned:
                pages.append({
                    "page_number": idx + 1,
                    "text": cleaned,
                })
    finally:
        doc.close()

    if not pages:
        raise PDFExtractionError(
            "No extractable text found in PDF. Scanned images or password-protected documents without OCR are not supported."
        )

    return pages


def chunk_extracted_pages(
    pages: List[Dict[str, Any]],
    doc_id: str,
    target_tokens: int = TARGET_CHUNK_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
    max_tokens: int = MAX_CHUNK_TOKENS,
) -> List[Dict[str, Any]]:
    """
    Splits extracted pages into semantic chunks respecting token limits.
    Keeps track of page numbers, token count, and chunk sequence.
    """
    tokenizer = get_tokenizer()
    chunks: List[Dict[str, Any]] = []

    # First pass: collect semantic blocks with page associations
    blocks: List[Tuple[str, int]] = []
    for p in pages:
        page_num = p["page_number"]
        page_text = p["text"]
        paragraphs = [para.strip() for para in page_text.split("\n\n") if para.strip()]
        for para in paragraphs:
            blocks.append((para, page_num))

    curr_texts: List[str] = []
    curr_tokens = 0
    curr_pages: List[int] = []

    def commit_chunk():
        nonlocal curr_texts, curr_tokens, curr_pages
        if not curr_texts:
            return
        content = "\n\n".join(curr_texts).strip()
        if not content:
            return

        c_tokens = len(tokenizer.encode(content))
        primary_page = curr_pages[0] if curr_pages else 1
        page_range = f"Page {primary_page}" if curr_pages[0] == curr_pages[-1] else f"Pages {curr_pages[0]}-{curr_pages[-1]}"

        chunks.append({
            "content": content,
            "token_count": c_tokens,
            "page_number": primary_page,
            "section": page_range,
        })

    for block_text, page_num in blocks:
        block_tokens = len(tokenizer.encode(block_text))

        # If a single paragraph exceeds max_tokens, slice it strictly
        if block_tokens > max_tokens:
            commit_chunk()
            curr_texts = []
            curr_tokens = 0
            curr_pages = []

            words = block_text.split(" ")
            w_acc: List[str] = []
            w_tokens = 0
            for w in words:
                wt = len(tokenizer.encode(w + " "))
                if w_tokens + wt > target_tokens and w_acc:
                    sub_content = " ".join(w_acc)
                    chunks.append({
                        "content": sub_content,
                        "token_count": len(tokenizer.encode(sub_content)),
                        "page_number": page_num,
                        "section": f"Page {page_num}",
                    })
                    w_acc = [w]
                    w_tokens = wt
                else:
                    w_acc.append(w)
                    w_tokens += wt
            if w_acc:
                sub_content = " ".join(w_acc)
                chunks.append({
                    "content": sub_content,
                    "token_count": len(tokenizer.encode(sub_content)),
                    "page_number": page_num,
                    "section": f"Page {page_num}",
                })
            continue

        if curr_tokens + block_tokens > target_tokens and curr_texts:
            commit_chunk()
            # Retain overlap from last text if available
            overlap_text = curr_texts[-1] if len(curr_texts) > 1 else ""
            overlap_tok = len(tokenizer.encode(overlap_text)) if overlap_text else 0
            if overlap_tok > 0 and overlap_tok <= overlap_tokens:
                curr_texts = [overlap_text, block_text]
                curr_tokens = overlap_tok + block_tokens
                curr_pages = [curr_pages[-1], page_num]
            else:
                curr_texts = [block_text]
                curr_tokens = block_tokens
                curr_pages = [page_num]
        else:
            curr_texts.append(block_text)
            curr_tokens += block_tokens
            curr_pages.append(page_num)

    commit_chunk()

    # Assign IDs and metadata to final chunks
    total_chunks = len(chunks)
    for idx, c in enumerate(chunks, start=1):
        c["chunk_id"] = f"{doc_id}_c{idx:03d}"
        c["chunk_index"] = idx
        c["total_chunks_in_doc"] = total_chunks
        c["metadata"] = {
            "chunk_index": idx,
            "total_chunks_in_doc": total_chunks,
            "token_count": c["token_count"],
            "page_number": c["page_number"],
            "section": c["section"],
            "document_id": doc_id,
        }

    return chunks


def format_halfvec(embedding: List[float]) -> str:
    """Formats float list to PostgreSQL halfvec string literal: '[x1,x2,...]'."""
    return f"[{','.join(f'{x:.7f}' for x in embedding)}]"


class PDFIngestionService:
    """
    Complete service for PDF validation, extraction, chunking, embedding,
    and database storage into Supabase pgvector.
    """

    def process_and_ingest_pdf(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end PDF ingestion pipeline.
        Idempotent: Detects duplicate uploads by content hash and returns existing status.
        """
        clean_name = sanitize_filename(filename)
        validate_pdf_bytes(file_bytes, clean_name)

        # Compute SHA-256 hash of file content for deterministic document ID
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        doc_id = f"upload_{file_hash[:16]}"

        conn = None
        try:
            conn = get_db_connection()

            # Step 1: Check for duplicate document
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, document_name FROM documents WHERE id = %s;",
                    (doc_id,),
                )
                existing_doc = cur.fetchone()

                if existing_doc:
                    cur.execute(
                        "SELECT COUNT(*) FROM document_chunks WHERE document_id = %s;",
                        (doc_id,),
                    )
                    count_row = cur.fetchone()
                    chunk_count = count_row[0] if count_row else 0
                    if chunk_count > 0:
                        logger.info(f"PDF {clean_name} ({doc_id}) already ingested with {chunk_count} chunks.")
                        return {
                            "status": "already_exists",
                            "document_id": doc_id,
                            "document_name": existing_doc[1] or clean_name,
                            "total_chunks": chunk_count,
                            "source_dataset": "uploaded_docs",
                            "message": f"Document '{clean_name}' has already been processed and indexed ({chunk_count} chunks).",
                        }

            # Step 2: Extract text from PDF
            pages = extract_text_from_pdf(file_bytes)
            total_pages = len(pages)

            # Step 3: Chunk text into target token lengths
            chunks = chunk_extracted_pages(pages, doc_id)
            if not chunks:
                raise PDFExtractionError("Failed to generate any valid text chunks from document.")

            logger.info(f"Extracted {len(chunks)} chunks across {total_pages} pages for {clean_name}.")

            # Step 4: Generate NVIDIA embeddings for all chunks in batches
            chunk_texts = [c["content"] for c in chunks]
            batch_size = 24
            all_embeddings: List[List[float]] = []

            for b_start in range(0, len(chunk_texts), batch_size):
                b_end = min(b_start + batch_size, len(chunk_texts))
                batch_passages = chunk_texts[b_start:b_end]
                embs = embedding_service.get_passage_embeddings(batch_passages)
                all_embeddings.extend(embs)

            if len(all_embeddings) != len(chunks):
                raise PDFIngestionError(
                    f"Generated {len(all_embeddings)} embeddings for {len(chunks)} chunks. Mismatch detected."
                )

            # Step 5: Store in Supabase PostgreSQL within a single atomic transaction
            with conn.cursor() as cur:
                # 5a. Insert parent document record
                cur.execute(
                    """
                    INSERT INTO documents (
                        id, document_name, document_type, source, source_dataset,
                        issued_date, regulation_area, applicable_to, created_at
                    ) VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        document_name = EXCLUDED.document_name;
                    """,
                    (
                        doc_id,
                        clean_name,
                        "Uploaded Document",
                        "Uploaded PDF",
                        "uploaded_docs",
                        "Uploaded Financial Document",
                        "User Uploaded Policy / Brochure",
                    ),
                )

                # 5b. Insert chunks with halfvec(2048) embeddings
                chunk_rows = []
                for ch, emb in zip(chunks, all_embeddings):
                    meta = ch["metadata"]
                    chunk_rows.append((
                        ch["chunk_id"],
                        doc_id,
                        ch["chunk_id"],
                        ch["content"],
                        ch["chunk_index"],
                        ch["total_chunks_in_doc"],
                        ch["token_count"],
                        ch["page_number"],
                        ch["section"],
                        format_halfvec(emb),
                        Json(meta),
                    ))

                insert_chunk_sql = """
                INSERT INTO document_chunks (
                    id, document_id, chunk_id, content, chunk_index,
                    total_chunks_in_doc, token_count, page_number, section,
                    embedding, metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::halfvec, %s, NOW())
                ON CONFLICT (chunk_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata;
                """
                execute_batch(cur, insert_chunk_sql, chunk_rows, page_size=50)

            conn.commit()
            logger.info(f"Successfully committed document {doc_id} with {len(chunks)} chunks.")

            total_tokens = sum(c["token_count"] for c in chunks)
            return {
                "status": "success",
                "document_id": doc_id,
                "document_name": clean_name,
                "total_pages": total_pages,
                "total_chunks": len(chunks),
                "total_tokens": total_tokens,
                "source_dataset": "uploaded_docs",
                "message": f"Successfully ingested '{clean_name}': {len(chunks)} chunks indexed across {total_pages} pages.",
            }

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"PDF ingestion failed for {filename}: {e}", exc_info=True)
            if isinstance(e, (PDFValidationError, PDFExtractionError, PDFIngestionError)):
                raise
            raise PDFIngestionError(f"Database insertion failed: {e}") from e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def list_uploaded_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieves all documents uploaded with source_dataset='uploaded_docs'.
        """
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        d.id,
                        d.document_name,
                        d.document_type,
                        d.source,
                        d.source_dataset,
                        d.created_at,
                        COUNT(dc.id) as chunk_count
                    FROM documents d
                    LEFT JOIN document_chunks dc ON d.id = dc.document_id
                    WHERE d.source_dataset = 'uploaded_docs'
                    GROUP BY d.id, d.document_name, d.document_type, d.source, d.source_dataset, d.created_at
                    ORDER BY d.created_at DESC;
                    """
                )
                rows = cur.fetchall()
                results = []
                for r in rows:
                    results.append({
                        "document_id": r[0],
                        "document_name": r[1],
                        "document_type": r[2],
                        "source": r[3],
                        "source_dataset": r[4],
                        "created_at": r[5].isoformat() if r[5] else None,
                        "chunk_count": r[6],
                    })
                return results
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def delete_uploaded_document(self, document_id: str) -> bool:
        """
        Deletes an uploaded document and its cascading chunks from pgvector.
        Only documents with source_dataset='uploaded_docs' can be deleted.
        """
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM documents
                    WHERE id = %s AND source_dataset = 'uploaded_docs'
                    RETURNING id;
                    """,
                    (document_id,),
                )
                deleted = cur.fetchone()
            conn.commit()
            return bool(deleted)
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# Singleton instance
pdf_ingestion_service = PDFIngestionService()
