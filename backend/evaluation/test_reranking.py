"""
Unit and integration tests for NVIDIA Reranking Service and Retrieval integration.

Tests:
1. Direct reranker API call with relevant vs irrelevant passages.
2. Verification of logit descending order and sigmoid probability computation.
3. Edge cases (empty passages, single passage).
4. Graceful fallback to vector retrieval when reranker encounters errors or is disabled.
5. End-to-end retrieval with and without reranking.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.reranking_service import RerankingService, reranking_service
from backend.app.services.retrieval_service import retrieval_service


def test_direct_reranking_accuracy():
    print("\n--- Test 1: Direct Reranker Accuracy & Scoring ---")
    query = "What are the RBI rules regarding KYC requirements?"
    passages = [
        "The Reserve Bank of India mandates Customer Due Diligence (CDD) and periodic KYC updates every 2 years for high-risk accounts.",
        "Farmers in Punjab harvest wheat during the spring season using combine harvesters.",
        "A bank account nominee can claim deposits upon submission of death certificate and KYC verification.",
    ]

    rankings = reranking_service.rerank(query, passages)
    assert len(rankings) == 3, f"Expected 3 rankings, got {len(rankings)}"

    # Top ranked passage must be index 0 (the KYC passage)
    top_result = rankings[0]
    assert top_result["index"] == 0, f"Expected index 0 at Rank 1, got {top_result['index']}"
    assert top_result["logit"] > rankings[1]["logit"], "Rank 1 logit should be higher than Rank 2"
    assert top_result["score"] > rankings[1]["score"], "Rank 1 score should be higher than Rank 2"
    assert 0.0 <= top_result["score"] <= 1.0, "Score should be in [0, 1] range"

    # Least relevant must be index 1 (wheat harvesting)
    lowest_result = rankings[-1]
    assert lowest_result["index"] == 1, f"Expected index 1 at lowest rank, got {lowest_result['index']}"

    print(f"✓ Reranker correctly scored and ranked passages:")
    for rank, r in enumerate(rankings, 1):
        preview = passages[r["index"]][:65]
        print(f"   Rank {rank}: [Index {r['index']}] Logit: {r['logit']:+.4f} | Prob: {r['score']:.4f} | {preview}...")


def test_reranker_empty_passages():
    print("\n--- Test 2: Reranker Edge Cases ---")
    # Empty passages
    res = reranking_service.rerank("What is KYC?", [])
    assert res == [], "Expected empty list for empty passages"

    # Single passage
    res_single = reranking_service.rerank("What is KYC?", ["KYC stands for Know Your Customer."])
    assert len(res_single) == 1
    assert res_single[0]["index"] == 0
    print("✓ Edge cases (empty list, single passage) handled correctly")


def test_retrieval_with_and_without_rerank():
    print("\n--- Test 3: End-to-End Retrieval With vs. Without Rerank ---")
    query = "What precautions should customers take to avoid digital arrest scams?"

    # Retrieval without rerank (vector only, top 5)
    vector_only = retrieval_service.retrieve(
        query,
        match_count=15,
        final_count=5,
        enable_rerank=False,
    )
    assert len(vector_only) == 5, f"Expected 5 chunks, got {len(vector_only)}"
    assert all(c.rerank_score is None for c in vector_only), "rerank_score should be None when rerank is False"

    # Retrieval with rerank (vector top 15 -> rerank top 5)
    reranked, is_reranked, total_cands = retrieval_service.retrieve(
        query,
        match_count=15,
        final_count=5,
        enable_rerank=True,
        return_metadata=True,
    )
    assert len(reranked) == 5, f"Expected 5 chunks, got {len(reranked)}"
    assert is_reranked is True, "Expected is_reranked to be True"
    assert total_cands >= 5, f"Expected at least 5 candidates, got {total_cands}"
    assert all(c.rerank_score is not None for c in reranked), "rerank_score should be populated"
    assert all(c.rerank_logit is not None for c in reranked), "rerank_logit should be populated"
    assert all(c.initial_rank is not None for c in reranked), "initial_rank should be populated"

    print(f"✓ Vector only retrieved {len(vector_only)} chunks (top sim: {vector_only[0].similarity:.4f})")
    print(f"✓ Reranked retrieved {len(reranked)} chunks from {total_cands} candidates:")
    for c in reranked[:3]:
        print(f"   Rank {c.rank} (was Vector #{c.initial_rank}): [{c.source_dataset}] {c.document_name[:40]} | Logit: {c.rerank_logit:+.4f} | Sim: {c.similarity:.4f}")


def test_graceful_fallback():
    print("\n--- Test 4: Graceful Fallback on Reranker Failure ---")
    query = "What are the rules related to bank account nominee?"

    # Instantiate a service with an invalid endpoint to simulate failure
    failing_reranker = RerankingService(endpoint="https://ai.api.nvidia.com/v1/invalid-endpoint-fail", timeout_seconds=2.0)
    
    # Temporarily monkeypatch reranking_service in retrieval_service
    import backend.app.services.retrieval_service as rs_mod
    original_service = rs_mod.reranking_service
    rs_mod.reranking_service = failing_reranker

    try:
        results, is_reranked, total = rs_mod.retrieval_service.retrieve(
            query,
            match_count=15,
            final_count=5,
            enable_rerank=True,
            return_metadata=True,
        )
        assert len(results) == 5, f"Expected fallback to 5 chunks, got {len(results)}"
        assert is_reranked is False, "Expected is_reranked to be False after fallback"
        print(f"✓ Fallback succeeded seamlessly: returned {len(results)} chunks using vector similarity order")
    finally:
        rs_mod.reranking_service = original_service


if __name__ == "__main__":
    test_direct_reranking_accuracy()
    test_reranker_empty_passages()
    test_retrieval_with_and_without_rerank()
    test_graceful_fallback()
    print("\n==================================================")
    print("ALL RERANKING SERVICE TESTS PASSED")
    print("==================================================")
