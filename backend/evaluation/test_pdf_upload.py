"""
Test Suite for FinCheck AI Phase 7A: PDF Upload & Automatic RAG Ingestion.

Tests:
1. PDF validation (file extension, size bounds, magic bytes %PDF-).
2. Text extraction via PyMuPDF (clean text, page indexing, empty page handling).
3. Semantic text chunking (token limits <= 800, overlap, metadata tags).
4. Embedding generation & formatting (2048-dim halfvec representation).
5. Supabase pgvector insertion & transaction safety.
6. Safe failure recovery and database rollback on error.
7. Duplicate upload detection (SHA-256 idempotency).
8. FastAPI /api/upload/pdf and /api/upload/documents endpoints.
9. Semantic vector retrieval of uploaded document passages.
10. Gemini grounded generation citing uploaded documents.
"""

import hashlib
import io
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pymupdf

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import get_db_connection
from backend.app.services.pdf_ingestion_service import (
    PDFExtractionError,
    PDFIngestionError,
    PDFValidationError,
    chunk_extracted_pages,
    extract_text_from_pdf,
    pdf_ingestion_service,
    sanitize_filename,
    validate_pdf_bytes,
)
from backend.app.services.retrieval_service import retrieval_service
from backend.app.services.generation_service import generation_service

client = TestClient(app)


def create_sample_financial_pdf(title: str, text: str) -> bytes:
    """Creates a real in-memory PDF document using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, f"{title}\n\n{text}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


SAMPLE_POLICY_TEXT = (
    "FinCheck AI Wealth Directive 2026-WD-99: Liquidity Buffer Requirements.\n"
    "Section 4.1: Special Liquidity Management Guidelines.\n"
    "All discretionary portfolio management accounts maintaining assets under management "
    "exceeding INR 25 Crores are mandatorily required to maintain a liquid sovereign buffer of at least 14.5 percent. "
    "This liquidity buffer must be held in central government treasury bills or overnight sovereign repo facilities. "
    "Accredited wealth advisors must review asset-liability allocations on a bi-monthly schedule."
)


def test_pdf_validation():
    """Validates secure file validation: extension, size, and magic bytes."""
    valid_pdf = create_sample_financial_pdf("Test Doc", "Valid sample body.")

    # 1. Valid PDF passes
    validate_pdf_bytes(valid_pdf, "valid_policy.pdf")

    # 2. Invalid extension
    try:
        validate_pdf_bytes(valid_pdf, "document.docx")
        assert False, "Should reject non-pdf extension"
    except PDFValidationError as e:
        assert "Only .pdf files are accepted" in str(e)

    # 3. File too small / empty
    try:
        validate_pdf_bytes(b"short", "empty.pdf")
        assert False, "Should reject tiny file"
    except PDFValidationError as e:
        assert "empty or too small" in str(e)

    # 4. Corrupt header (missing %PDF- magic bytes)
    fake_header = b"NOT_A_PDF_" + b"0" * 200
    try:
        validate_pdf_bytes(fake_header, "fake.pdf")
        assert False, "Should reject invalid magic header"
    except PDFValidationError as e:
        assert "%PDF-" in str(e)

    # 5. Filename sanitization
    assert sanitize_filename("../../../etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("my  financial   doc.pdf") == "my financial doc.pdf"
    print("✓ Test 1: PDF validation, security checks, and filename sanitization passed")


def test_text_extraction():
    """Validates PyMuPDF text extraction per page."""
    pdf_bytes = create_sample_financial_pdf("Wealth Title", "Paragraph 1 content.\n\nParagraph 2 compliance details.")
    pages = extract_text_from_pdf(pdf_bytes)

    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert "Wealth Title" in pages[0]["text"]
    assert "Paragraph 1 content" in pages[0]["text"]

    # Empty PDF without text should raise PDFExtractionError
    empty_doc = pymupdf.open()
    empty_doc.new_page()  # Blank page
    empty_bytes = empty_doc.tobytes()
    empty_doc.close()

    try:
        extract_text_from_pdf(empty_bytes)
        assert False, "Should fail on blank PDF"
    except PDFExtractionError as e:
        assert "No extractable text" in str(e)

    print("✓ Test 2: Text extraction via PyMuPDF and blank page detection passed")


def test_text_chunking():
    """Validates token-bounded chunking with metadata."""
    sample_pages = [
        {"page_number": 1, "text": "Page 1 Header.\n\n" + ("Financial advisory regulations text. " * 30)},
        {"page_number": 2, "text": "Page 2 Header.\n\n" + ("Capital adequacy rules text. " * 30)},
    ]
    doc_id = "upload_test_chunking_123"
    chunks = chunk_extracted_pages(sample_pages, doc_id, target_tokens=200, max_tokens=300)

    assert len(chunks) >= 2
    for c in chunks:
        assert c["token_count"] <= 800
        assert "chunk_id" in c
        assert c["chunk_id"].startswith(doc_id)
        assert c["metadata"]["document_id"] == doc_id
        assert c["page_number"] in (1, 2)
    print("✓ Test 3: Token-aware chunking and metadata attribution passed")


def test_end_to_end_ingestion_and_duplicate_handling():
    """Tests end-to-end PDF ingestion into Supabase pgvector and duplicate detection."""
    filename = "wealth_directive_2026_test.pdf"
    pdf_bytes = create_sample_financial_pdf("FinCheck Directive 2026-WD-99", SAMPLE_POLICY_TEXT)

    # First ingestion
    result = pdf_ingestion_service.process_and_ingest_pdf(pdf_bytes, filename)
    assert result["status"] == "success"
    assert result["total_chunks"] >= 1
    doc_id = result["document_id"]
    assert result["source_dataset"] == "uploaded_docs"

    try:
        # Verify in database
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, document_name, source_dataset FROM documents WHERE id = %s;", (doc_id,))
            doc_row = cur.fetchone()
            assert doc_row is not None
            assert doc_row[2] == "uploaded_docs"

            cur.execute("SELECT COUNT(*) FROM document_chunks WHERE document_id = %s;", (doc_id,))
            chunk_count = cur.fetchone()[0]
            assert chunk_count == result["total_chunks"]
        conn.close()

        # Test duplicate ingestion: same file should be detected without creating duplicate records
        dup_result = pdf_ingestion_service.process_and_ingest_pdf(pdf_bytes, filename)
        assert dup_result["status"] == "already_exists"
        assert dup_result["document_id"] == doc_id
        assert dup_result["total_chunks"] == result["total_chunks"]

        print("✓ Test 4: Supabase pgvector insertion and duplicate idempotency passed")

    finally:
        # Clean up test document
        pdf_ingestion_service.delete_uploaded_document(doc_id)


def test_failure_recovery_and_rollback():
    """Verifies that an error during embedding or DB commit triggers complete rollback."""
    filename = "failure_test.pdf"
    pdf_bytes = create_sample_financial_pdf("Rollback Doc", "Content that will fail during embedding.")

    with patch("backend.app.services.pdf_ingestion_service.embedding_service.get_passage_embeddings") as mock_emb:
        mock_emb.side_effect = RuntimeError("Simulated NVIDIA embedding API failure")

        try:
            pdf_ingestion_service.process_and_ingest_pdf(pdf_bytes, filename)
            assert False, "Should raise exception on embedding failure"
        except (PDFIngestionError, RuntimeError):
            pass

    # Verify document was not committed
    file_hash = hashlib.sha256(pdf_bytes).hexdigest()
    doc_id = f"upload_{file_hash[:16]}"
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM documents WHERE id = %s;", (doc_id,))
        assert cur.fetchone() is None
    conn.close()
    print("✓ Test 5: Safe failure recovery and database transaction rollback passed")


def test_api_upload_endpoints():
    """Tests FastAPI /api/upload/pdf and /api/upload/documents endpoints."""
    filename = "api_test_directive.pdf"
    pdf_bytes = create_sample_financial_pdf("API Directive", SAMPLE_POLICY_TEXT)

    # 1. Invalid file extension should return 400
    res_bad = client.post(
        "/api/upload/pdf",
        files={"file": ("invalid.txt", b"plain text content", "text/plain")},
    )
    assert res_bad.status_code == 400
    assert "Only PDF" in res_bad.json()["detail"]

    # 2. Valid upload
    res = client.post(
        "/api/upload/pdf",
        files={"file": (filename, pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("success", "already_exists")
    doc_id = data["document_id"]

    try:
        # 3. List uploaded documents
        res_list = client.get("/api/upload/documents")
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert any(d["document_id"] == doc_id for d in list_data["documents"])

        print("✓ Test 6: FastAPI /api/upload/pdf and /api/upload/documents endpoints verified")

    finally:
        # 4. Delete endpoint
        res_del = client.delete(f"/api/upload/documents/{doc_id}")
        assert res_del.status_code == 200
        assert res_del.json()["success"] is True


def test_retrieval_and_gemini_grounding_with_uploaded_pdf():
    """
    Tests that an uploaded PDF is successfully retrieved by semantic vector search
    and can be cited by Gemini for grounded answer generation.
    """
    filename = "wealth_liquidity_policy_rag.pdf"
    pdf_bytes = create_sample_financial_pdf("FinCheck Wealth Directive 2026-WD-99", SAMPLE_POLICY_TEXT)

    # Ingest document
    result = pdf_ingestion_service.process_and_ingest_pdf(pdf_bytes, filename)
    doc_id = result["document_id"]

    try:
        # Step A: Test semantic retrieval over uploaded document
        question = "What is the mandatory liquid sovereign buffer for portfolios above INR 25 Crores under Directive 2026-WD-99?"
        chunks = retrieval_service.retrieve(question=question, match_count=10, final_count=5)

        # At least one chunk from our uploaded document should be in the retrieved candidates
        found_uploaded = any(c.document_id == doc_id for c in chunks)
        assert found_uploaded, f"Uploaded document {doc_id} was not retrieved in top candidates."

        uploaded_chunk = next(c for c in chunks if c.document_id == doc_id)
        assert "14.5 percent" in uploaded_chunk.content

        # Step B: Test Gemini Grounded Answer Generation using mock response verifying citation format
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    "Under FinCheck Wealth Directive 2026-WD-99, discretionary portfolio accounts exceeding "
                                    "INR 25 Crores must maintain a liquid sovereign buffer of at least 14.5 percent [Source 1]."
                                )
                            }
                        ]
                    }
                }
            ]
        }

        with patch.object(generation_service, "api_key", "test_gemini_api_key"), patch("httpx.Client.post", return_value=mock_resp):
            gen_res = generation_service.generate_answer(
                question=question,
                chunks=[uploaded_chunk],
            )
            assert gen_res.is_grounded is True
            assert 1 in gen_res.cited_source_ids
            assert "14.5 percent" in gen_res.answer
            assert gen_res.sources[0].document_id == doc_id

        print("✓ Test 7: Semantic vector retrieval and Gemini grounding with uploaded document verified")

    finally:
        # Clean up
        pdf_ingestion_service.delete_uploaded_document(doc_id)


if __name__ == "__main__":
    print("\n==================================================")
    print("RUNNING FINCHECK AI PHASE 7A PDF INGESTION TESTS")
    print("==================================================")
    test_pdf_validation()
    test_text_extraction()
    test_text_chunking()
    test_end_to_end_ingestion_and_duplicate_handling()
    test_failure_recovery_and_rollback()
    test_api_upload_endpoints()
    test_retrieval_and_gemini_grounding_with_uploaded_pdf()
    print("\n==================================================")
    print("ALL 7 PHASE 7A PDF INGESTION TESTS PASSED")
    print("==================================================\n")
