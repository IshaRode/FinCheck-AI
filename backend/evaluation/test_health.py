"""
Automated tests for the /health endpoint.
Verifies HTTP status 200 and expected response payload.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") == "healthy", f"Expected status 'healthy', got '{data.get('status')}'"
    assert data.get("service") == "FinCheck AI API", f"Expected service 'FinCheck AI API', got '{data.get('service')}'"
    print("✓ GET /health test passed successfully")


def test_api_health_endpoint_alias():
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") == "healthy"
    assert data.get("service") == "FinCheck AI API"
    print("✓ GET /api/health alias test passed successfully")


if __name__ == "__main__":
    test_health_endpoint()
    test_api_health_endpoint_alias()
    print("\nAll health check tests passed.")
