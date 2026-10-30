import pytest
from implementation.core.security import create_access_token
from implementation.core.config import settings

@pytest.mark.asyncio
async def test_intern_dashboard_blocks_unauthenticated(client):
    """
    CRITICAL ACCESS CONTROL ASSERTION:
    Verifies that unauthenticated callers receive HTTP 401 Unauthorized,
    preventing the proprietary curriculum/challenge leak observed in Next.js SSG.
    """
    response = await client.get("/api/v1/intern/dashboard")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]

@pytest.mark.asyncio
async def test_intern_dashboard_allows_authenticated_user(client, test_user):
    """Verifies that valid JWT session cookie allows access to learning materials."""
    token = create_access_token(data={"sub": test_user.id, "role": test_user.role, "email": test_user.email})
    client.cookies.set(settings.COOKIE_NAME, token)
    
    response = await client.get("/api/v1/intern/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "authorized"
    assert data["intern"]["email"] == test_user.email
    assert "curriculum" in data
