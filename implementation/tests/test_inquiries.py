import pytest

@pytest.mark.asyncio
async def test_submit_valid_inquiry(client):
    """Verifies successful ingestion of a business inquiry."""
    payload = {
        "fullName": "Jane Doe",
        "email": "jane.doe@enterprise.com",
        "company": "Fintech Global",
        "industry": "Finance",
        "message": "We would like to explore Cynbit's cloud architectural audit services."
    }
    response = await client.post("/api/v1/inquiries", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["inquiry_id"] is not None

@pytest.mark.asyncio
async def test_submit_inquiry_invalid_email(client):
    """Verifies that Pydantic rejects invalid email formats with 422 Unprocessable Entity."""
    payload = {
        "fullName": "Bad Actor",
        "email": "not-an-email-address",
        "message": "Testing payload validation"
    }
    response = await client.post("/api/v1/inquiries", json=payload)
    assert response.status_code == 422
