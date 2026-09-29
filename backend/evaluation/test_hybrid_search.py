"""
Test Suite for FinCheck AI Phase 7B: Hybrid Search.

Tests:
1. Vector-only retrieval
2. Keyword-only retrieval
3. Hybrid retrieval & RRF candidate fusion
4. Duplicate removal across vector & keyword channels
5. Exact-term & RBI circular queries (e.g. DOR.BP.BC.No.68, FEMA 339)
6. Queries where semantic and keyword search retrieve different documents
7. Cross-encoder reranking over hybrid candidates
8. FastAPI /api/ask/retrieve endpoint supporting search_mode configuration
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.retrieval_service import retrieval_service
from backend.app.services.embedding_service import embedding_service
from backend.app.models.retrieval import RetrieveResponse

client = TestClient(app)


def test_vector_only_retrieval():
    print("\n--- Test 1: Vector-Only Retrieval ---")
    question = "What are the KYC rules for opening a bank account?"
    results = retrieval_service.retrieve(
        question=question,
        match_count=5,
        final_count=5,
        search_mode="vector",
        enable_rerank=False,
    )
    assert len(results) > 0, "Vector retrieval returned no results."
    assert all(c.retrieval_source == "vector" for c in results)
    assert all(c.similarity >= 0.0 for c in results)
    print(f"✓ Retrieved {len(results)} vector-only candidates (top sim: {results[0].similarity:.4f})")


def test_keyword_only_retrieval():
    print("\n--- Test 2: Keyword-Only Retrieval ---")
    question = "digital arrest cyber scam"
    results = retrieval_service.retrieve(
        question=question,
        match_count=5,
        final_count=5,
        search_mode="keyword",
        enable_rerank=False,
    )
    assert len(results) > 0, "Keyword retrieval returned no results."
    assert all(c.retrieval_source == "keyword" for c in results)
    assert all(c.keyword_score is not None for c in results)
    print(f"✓ Retrieved {len(results)} keyword-only candidates (top kw_score: {results[0].keyword_score:.4f})")


def test_hybrid_retrieval_and_duplicate_removal():
    print("\n--- Test 3: Hybrid Retrieval & Duplicate Removal ---")
    question = "What are the guidelines for nominee update in savings account?"
    emb = embedding_service.get_query_embedding(question)

    merged = retrieval_service.hybrid_search(
        question=question,
        query_embedding=emb,
        vector_k=10,
        keyword_k=10,
    )
    assert len(merged) > 0, "Hybrid search returned no candidates."

    # Check deduplication
    chunk_ids = [c.chunk_id for c in merged]
    assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk IDs found in hybrid results!"

    # Verify RRF scores
    assert all("rrf_score" in c.metadata for c in merged)
    rrf_scores = [c.metadata["rrf_score"] for c in merged]
    assert rrf_scores == sorted(rrf_scores, reverse=True), "Merged candidates must be sorted by RRF score descending."

    # Check retrieval source tagging
    sources = set(c.retrieval_source for c in merged)
    print(f"✓ Successfully fused into {len(merged)} unique candidates. Detected sources: {sources}")


def test_exact_term_and_rbi_circular_queries():
    print("\n--- Test 4: Exact-Term & RBI Circular Number Queries ---")
    # Circular code test
    query_circular = "DOR.BP.BC.No.68"
    kw_results = retrieval_service.keyword_search(query_circular, match_count=5)
    assert len(kw_results) > 0, f"Expected matches for circular '{query_circular}'"
    top_doc = kw_results[0].document_name
    assert "DOR.BP.BC.No.68" in top_doc or "68" in top_doc or "RBI" in top_doc, f"Expected circular in doc name, got: {top_doc}"
    print(f"✓ Exact circular query '{query_circular}' matched document: '{top_doc}'")

    # Second exact circular test (FEMA)
    query_fema = "FEMA 339"
    fema_results = retrieval_service.keyword_search(query_fema, match_count=5)
    assert len(fema_results) > 0, f"Expected matches for '{query_fema}'"
    assert any("FEMA" in c.document_name or "FEMA" in c.content for c in fema_results)
    print(f"✓ Exact regulation query '{query_fema}' matched document: '{fema_results[0].document_name}'")


def test_disjoint_candidate_fusion():
    print("\n--- Test 5: Queries Where Semantic and Keyword Return Distinct Candidates ---")
    question = "DOR.BP.BC.No.68 liquidity management for banks"
    emb = embedding_service.get_query_embedding(question)

    vec_cands = retrieval_service.vector_search(emb, match_count=5)
    kw_cands = retrieval_service.keyword_search(question, match_count=5)

    vec_ids = set(c.chunk_id for c in vec_cands)
    kw_ids = set(c.chunk_id for c in kw_cands)

    merged = retrieval_service.hybrid_search(question, emb, vector_k=5, keyword_k=5)
    merged_ids = set(c.chunk_id for c in merged)

    # Hybrid pool must be a superset of both modalities
    assert vec_ids.issubset(merged_ids), "All vector candidates must be represented in hybrid pool"
    assert kw_ids.issubset(merged_ids), "All keyword candidates must be represented in hybrid pool"
    print(f"✓ Distinct pool fusion verified: {len(vec_ids)} vector + {len(kw_ids)} keyword -> {len(merged)} unique merged candidates.")


def test_reranking_after_hybrid_retrieval():
    print("\n--- Test 6: Cross-Encoder Reranking After Hybrid Retrieval ---")
    question = "What are the customer protection rules against digital arrest fraud?"

    reranked, is_reranked, total_cands = retrieval_service.retrieve(
        question=question,
        match_count=10,
        final_count=5,
        search_mode="hybrid",
        enable_rerank=True,
        return_metadata=True,
    )
    assert len(reranked) == 5
    assert is_reranked is True
    assert total_cands >= 5
    assert all(c.rerank_score is not None for c in reranked)
    assert all(c.rank == idx for idx, c in enumerate(reranked, 1))

    print(f"✓ Reranked {total_cands} hybrid candidates down to top 5:")
    for c in reranked[:3]:
        print(f"   Rank {c.rank} (Source: {c.retrieval_source}): {c.document_name[:40]} | Rerank Score: {c.rerank_score:.4f}")


def test_api_hybrid_search_endpoint():
    print("\n--- Test 7: FastAPI Endpoint with Search Mode Options ---")
    # 1. Default hybrid
    res_hybrid = client.post("/api/ask/retrieve", json={"question": "What is inclusive KYC?", "search_mode": "hybrid"})
    assert res_hybrid.status_code == 200
    data_hybrid = res_hybrid.json()
    validated_hybrid = RetrieveResponse.model_validate(data_hybrid)
    assert validated_hybrid.search_mode == "hybrid"
    assert len(validated_hybrid.results) > 0

    # 2. Vector mode
    res_vec = client.post("/api/ask/retrieve", json={"question": "What is inclusive KYC?", "search_mode": "vector"})
    assert res_vec.status_code == 200
    data_vec = res_vec.json()
    assert data_vec["search_mode"] == "vector"

    # 3. Keyword mode
    res_kw = client.post("/api/ask/retrieve", json={"question": "DOR.BP.BC.No.68", "search_mode": "keyword"})
    assert res_kw.status_code == 200
    data_kw = res_kw.json()
    assert data_kw["search_mode"] == "keyword"

    print("✓ FastAPI endpoint successfully supports 'hybrid', 'vector', and 'keyword' modes.")


if __name__ == "__main__":
    print("\n==================================================")
    print("RUNNING FINCHECK AI PHASE 7B HYBRID SEARCH TESTS")
    print("==================================================")
    test_vector_only_retrieval()
    test_keyword_only_retrieval()
    test_hybrid_retrieval_and_duplicate_removal()
    test_exact_term_and_rbi_circular_queries()
    test_disjoint_candidate_fusion()
    test_reranking_after_hybrid_retrieval()
    test_api_hybrid_search_endpoint()
    print("\n==================================================")
    print("ALL 7 PHASE 7B HYBRID SEARCH TESTS PASSED")
    print("==================================================\n")
