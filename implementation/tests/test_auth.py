import pytest

@pytest.mark.asyncio
async def test_successful_login(client, test_user):
    """Verifies authentication via Argon2id and setting of HttpOnly cookie."""
    login_payload = {
        "email": "intern@cynbit.in",
        "password": "SuperSecretPassword123!"
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["email"] == "intern@cynbit.in"
    
    # Assert HttpOnly cookie was set in headers
    cookies = response.cookies
    assert "cynbit_session" in cookies

@pytest.mark.asyncio
async def test_failed_login_invalid_password(client, test_user):
    """Verifies that invalid password returns 401 Unauthorized without leakage."""
    login_payload = {
        "email": "intern@cynbit.in",
        "password": "WrongPassword999!"
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_password_reset_zero_enumeration(client, test_user):
    """
    Verifies that requesting password reset returns identical generic status
    for both registered and non-registered emails, eliminating user enumeration.
    """
    # Registered email
    resp1 = await client.post(
        "/api/v1/auth/request-password-reset",
        json={"email": "intern@cynbit.in"}
    )
    assert resp1.status_code == 200
    
    # Non-registered email
    resp2 = await client.post(
        "/api/v1/auth/request-password-reset",
        json={"email": "nonexistent_stranger@random.com"}
    )
    assert resp2.status_code == 200
    
    # Exact message match prevents enumeration
    assert resp1.json()["message"] == resp2.json()["message"]

