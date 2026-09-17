"""
Automated unit and integration tests for the FastAPI retrieval endpoint.
Validates:
- Validation on empty or malformed inputs
- End-to-end retrieval for the 3 domain queries
- Strict Pydantic response schema conformance
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.retrieval import RetrieveResponse

client = TestClient(app)

TEST_QUERIES = [
    "What are the RBI rules regarding KYC requirements?",
    "What precautions should customers take to avoid digital arrest scams?",
    "What are the rules related to bank account nominee?",
]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FinCheck AI API"

    response_alias = client.get("/api/health")
    assert response_alias.status_code == 200
    assert response_alias.json()["status"] == "healthy"
    print("✓ Health check endpoint (/health and /api/health) passed")


def test_empty_question_validation():
    # Test 1: Empty string
    response = client.post("/api/ask/retrieve", json={"question": ""})
    assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"

    # Test 2: Whitespace only
    response = client.post("/api/ask/retrieve", json={"question": "   "})
    assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"

    # Test 3: Missing question field
    response = client.post("/api/ask/retrieve", json={})
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    # Test 4: Too short (< 3 chars)
    response = client.post("/api/ask/retrieve", json={"question": "ab"})
    assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"

    # Test 5: Too long (> 1000 chars)
    long_question = "What are the rules regarding " + "a" * 1050 + "?"
    response = client.post("/api/ask/retrieve", json={"question": long_question})
    assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"

    # Ensure error response does not expose internal secrets
    err_body = response.text.lower()
    assert "password" not in err_body
    assert "secret" not in err_body
    assert "nvapi-" not in err_body

    print("✓ Request validation on invalid/empty/length inputs and error safety passed")


def test_retrieval_queries():
    for idx, query in enumerate(TEST_QUERIES, 1):
        print(f"\n--- Testing Query #{idx}: \"{query}\" ---")
        response = client.post("/api/ask/retrieve", json={"question": query})
        assert response.status_code == 200, f"Failed for query '{query}': {response.status_code} {response.text}"

        data = response.json()

        # Validate with Pydantic model
        validated = RetrieveResponse.model_validate(data)
        assert validated.question == query
        assert len(validated.results) > 0, "No results returned"
        assert len(validated.results) <= 10, "More than 10 results returned"

        print(f"✓ Retrieved {len(validated.results)} chunks successfully:")
        for r in validated.results[:3]:
            print(f"   Rank {r.rank}: [{r.source_dataset}] {r.document_name} | Sim: {r.similarity:.4f}")
            print(f"          Preview: {r.content[:90]}...")

    print("\n✓ All 3 test queries passed with valid Pydantic schema and top 10 chunks")


if __name__ == "__main__":
    test_health_check()
    test_empty_question_validation()
    test_retrieval_queries()
    print("\n==================================================")
    print("ALL RETRIEVAL ENDPOINT TESTS PASSED")
    print("==================================================")
