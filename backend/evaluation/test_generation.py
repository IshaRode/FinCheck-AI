"""
Test Suite for Grounded Answer Generation with Gemini in FinCheck AI.
Tests:
1. Strict prompt construction (RBI priority, source labeling, grounding constraints).
2. Citation extraction regex logic ([Source N]).
3. Insufficient context detection patterns.
4. Graceful fallback on API timeout/error without user-facing crash.
5. End-to-end FastAPI endpoint (/api/ask/generate) validation.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.retrieval import RetrievedChunk
from backend.app.services.generation_service import (
    GenerationError,
    generation_service,
)

client = TestClient(app)

SAMPLE_CHUNKS = [
    RetrievedChunk(
        rank=1,
        chunk_id="rbi_c001",
        document_id="doc_rbi_104",
        document_name="RBI Circular 2024-2025/104 - Deceased Accounts",
        source="RBI",
        source_dataset="rbi",
        content=(
            "Banks shall settle the claims in respect of deceased depositors within a period not "
            "exceeding 15 days from the date of receipt of the claim along with all requisite documents. "
            "For accounts with nomination, payment shall be made to the nominee upon verification of death certificate."
        ),
        similarity=0.742,
        rerank_score=0.941,
        rerank_logit=2.78,
        initial_rank=3,
        metadata={"section": "Settlement Timeline"},
    ),
    RetrievedChunk(
        rank=2,
        chunk_id="indfin_c002",
        document_id="doc_indfin_pension",
        document_name="Pension & Senior Citizen Banking Guide",
        source="Indian Finance",
        source_dataset="indian_finance",
        content=(
            "A nominee acts as a trustee of the funds and is legally obligated to transfer the proceeds "
            "to the legal heirs of the deceased account holder in accordance with succession laws."
        ),
        similarity=0.685,
        rerank_score=0.812,
        rerank_logit=1.46,
        initial_rank=5,
        metadata={"section": "Legal Role of Nominee"},
    ),
]


def test_prompt_construction():
    """Verifies that the prompt builder enforces regulatory priority and grounding."""
    system_inst, user_prompt = generation_service.build_prompt(
        "What is the maximum timeline for settlement of deceased depositor claims?",
        SAMPLE_CHUNKS,
    )

    # 1. System instruction checks
    assert "STRICT GROUNDING" in system_inst
    assert "REGULATORY PRIORITY" in system_inst
    assert "Reserve Bank of India (RBI)" in system_inst
    assert "MANDATORY CITATIONS" in system_inst
    assert "INSUFFICIENT CONTEXT" in system_inst

    # 2. User prompt checks
    assert "[Source 1] (Dataset: RBI Circular" in user_prompt
    assert "[Source 2] (Dataset: Indian Finance" in user_prompt
    assert "RBI Circular 2024-2025/104" in user_prompt
    assert "15 days" in user_prompt
    assert "What is the maximum timeline" in user_prompt
    print("✓ Test 1: Strict prompt construction verified")


def test_citation_extraction():
    """Verifies that [Source N] citations are extracted accurately and deduplicated."""
    answer_text = (
        "Under RBI guidelines, banks must settle deceased depositor claims within 15 days [Source 1]. "
        "The nominee acts as a custodian or trustee of the funds [Source 2]. "
        "Upon verification of the death certificate, the balance is released [Source 1]."
    )

    cited = generation_service.extract_citations(answer_text)
    assert cited == [1, 2], f"Expected [1, 2], got {cited}"

    # Edge cases
    empty_cited = generation_service.extract_citations("No citations here.")
    assert empty_cited == []

    multi_cited = generation_service.extract_citations(
        "Refer to [Source 5], [Source 3], and [source 1]."
    )
    assert multi_cited == [1, 3, 5]
    print("✓ Test 2: Citation extraction logic verified")


def test_insufficient_context_detection():
    """Verifies detection of model declaring insufficient context in bank documents."""
    insufficient_samples = [
        "The provided bank documents do not contain sufficient information to answer this question.",
        "There is insufficient context available in the provided circulars regarding gold loan LTV.",
        "The provided documents do not mention interest rate subsidies for green car loans.",
    ]

    for sample in insufficient_samples:
        assert generation_service.is_insufficient_context(sample) is True, f"Failed on: {sample}"

    sufficient_sample = (
        "As per RBI Circular 2024/104 [Source 1], banks must settle claims within 15 days."
    )
    assert generation_service.is_insufficient_context(sufficient_sample) is False
    print("✓ Test 3: Insufficient context detection verified")


def test_fallback_response_creation():
    """Verifies that create_fallback_response gracefully presents sources with is_grounded=False."""
    fallback = generation_service.create_fallback_response(
        question="What is the deposit insurance limit?",
        chunks=SAMPLE_CHUNKS,
        reason="Gemini API timed out after 30s",
        total_candidates=15,
        reranked=True,
    )

    assert fallback.is_grounded is False
    assert fallback.is_insufficient_context is False
    assert len(fallback.sources) == 2
    assert "temporarily unavailable" in fallback.answer
    assert "Gemini API timed out" in fallback.answer
    assert fallback.reranked is True
    print("✓ Test 4: Graceful fallback response structure verified")


def test_api_generate_endpoint_validation():
    """Verifies request validation on /api/ask/generate."""
    # 1. Blank question -> 422 (Pydantic validation error) or 400
    res = client.post("/api/ask/generate", json={"question": "   "})
    assert res.status_code in (400, 422)

    # 2. Health check still works
    res_health = client.get("/health")
    assert res_health.status_code == 200
    print("✓ Test 5: API endpoint input validation verified")


def test_api_generate_with_mocked_gemini():
    """Verifies end-to-end endpoint execution with mocked Gemini response."""
    mock_gemini_answer = (
        "Under official RBI guidelines, claims on deceased depositors' accounts must be settled "
        "within a maximum period of 15 days from receipt of all required documents [Source 1]. "
        "The nominee acts as a trustee for the legal heirs [Source 2]."
    )

    with patch.object(generation_service, "generate_answer") as mock_gen:
        mock_gen.return_value = generation_service.create_fallback_response(
            question="What is the claim settlement timeline?",
            chunks=SAMPLE_CHUNKS,
            reason="Mocked",
        )
        # Override answer
        mock_gen.return_value.answer = mock_gemini_answer
        mock_gen.return_value.is_grounded = True
        mock_gen.return_value.cited_source_ids = [1, 2]

        res = client.post(
            "/api/ask/generate",
            json={"question": "What is the claim settlement timeline?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["question"] == "What is the claim settlement timeline?"
        assert "[Source 1]" in data["answer"]
        assert data["is_grounded"] is True
        assert data["cited_source_ids"] == [1, 2]
        assert len(data["sources"]) > 0

    print("✓ Test 6: End-to-end API generation with citation mapping verified")


def test_api_generate_graceful_fallback_on_gemini_error():
    """Verifies that an error in Gemini generation safely falls back to returning sources with HTTP 200."""
    with patch.object(
        generation_service, "generate_answer", side_effect=GenerationError("Simulated connection timeout")
    ):
        res = client.post(
            "/api/ask/generate",
            json={"question": "What are the rules for high risk KYC update?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_grounded"] is False
        assert "temporarily unavailable" in data["answer"]
        assert len(data["sources"]) > 0
    print("✓ Test 7: API graceful fallback on generation error verified")


def test_api_generate_with_insufficient_context():
    """Verifies that an insufficient context answer sets is_insufficient_context=True and is_grounded=False."""
    mock_insufficient_answer = (
        "The provided bank documents do not contain sufficient information to answer this question. "
        "The retrieved passages discuss deposit accounts but contain no details regarding cryptocurrency leasing."
    )

    with patch.object(generation_service, "generate_answer") as mock_gen:
        mock_gen.return_value = generation_service.create_fallback_response(
            question="What is the policy on crypto leasing?",
            chunks=SAMPLE_CHUNKS,
            reason="Mocked",
        )
        mock_gen.return_value.answer = mock_insufficient_answer
        mock_gen.return_value.is_grounded = False
        mock_gen.return_value.is_insufficient_context = True

        res = client.post(
            "/api/ask/generate",
            json={"question": "What is the policy on crypto leasing?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_insufficient_context"] is True
        assert data["is_grounded"] is False
        assert "do not contain sufficient information" in data["answer"]
    print("✓ Test 8: Insufficient context handling through API verified")


if __name__ == "__main__":
    print("\n==================================================")
    print("RUNNING FINCHECK AI PHASE 6 GENERATION TESTS")
    print("==================================================")
    test_prompt_construction()
    test_citation_extraction()
    test_insufficient_context_detection()
    test_fallback_response_creation()
    test_api_generate_endpoint_validation()
    test_api_generate_with_mocked_gemini()
    test_api_generate_graceful_fallback_on_gemini_error()
    test_api_generate_with_insufficient_context()
    print("\n==================================================")
    print("ALL 8 GENERATION SERVICE TESTS PASSED")
    print("==================================================\n")
