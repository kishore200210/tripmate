from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test that the application starts and the health endpoint is responsive."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_openapi_schema():
    """Test that the OpenAPI schema is generated correctly with all registered routers."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    
    # Verify standard metadata
    assert schema["info"]["title"] == "TripMate"
    
    # Verify routers are registered
    paths = schema.get("paths", {})
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/destinations/" in paths
    assert "/api/v1/trips/" in paths
    assert "/api/v1/vision/analyze" in paths
