import pytest

@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    """Verifies that the /health endpoint responds with 200 OK and database status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cynbit-backend-api"
    assert "database" in data

@pytest.mark.asyncio
async def test_security_headers_injected(client):
    """Verifies that the custom SecurityHeadersMiddleware injects all required security headers."""
    response = await client.get("/api/v1/health")
    headers = response.headers
    
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers.get("Permissions-Policy", "")
    assert "max-age=63072000" in headers.get("Strict-Transport-Security", "")
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
