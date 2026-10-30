import hmac
import hashlib
import base64
import json
import pytest
from implementation.core.config import settings

@pytest.mark.asyncio
async def test_create_payment_order(client):
    """Verifies Cashfree order session creation."""
    payload = {
        "candidateName": "Rohit Verma",
        "email": "rohit.verma@test.com",
        "phone": "9876543210",
        "college": "IIT Delhi",
        "track": "Backend Engineering",
        "amount": 4999.00
    }
    response = await client.post("/api/v1/payments/create-order", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "ORDER_" in data["orderId"]
    assert "session_" in data["paymentSessionId"]

@pytest.mark.asyncio
async def test_valid_cashfree_webhook_signature(client):
    """Verifies successful order settlement upon authentic HMAC-SHA256 signed webhook."""
    # First create an order
    create_res = await client.post("/api/v1/payments/create-order", json={
        "candidateName": "Pooja Sharma",
        "email": "pooja.sharma@test.com",
        "phone": "9123456789",
        "college": "BITS Pilani",
        "track": "AI Systems",
        "amount": 4999.00
    })
    order_id = create_res.json()["orderId"]
    
    # Construct authentic webhook payload
    webhook_dict = {
        "data": {
            "order": {
                "order_id": order_id,
                "order_status": "PAID",
                "order_amount": 4999.00
            },
            "payment": {
                "payment_status": "SUCCESS"
            }
        },
        "event_time": "2026-10-30T14:30:00Z",
        "type": "PAYMENT_SUCCESS_WEBHOOK"
    }
    raw_body = json.dumps(webhook_dict).encode("utf-8")
    
    # Compute authentic HMAC-SHA256 signature
    digest = hmac.new(
        settings.CASHFREE_SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).digest()
    valid_sig = base64.b64encode(digest).decode("utf-8")
    
    response = await client.post(
        "/api/v1/payments/cashfree-webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "x-webhook-signature": valid_sig
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_forged_cashfree_webhook_signature_rejected(client):
    """Verifies that spoofed or tampered webhooks are rejected with 400 Bad Request."""
    raw_body = b'{"data": {"order": {"order_id": "ORDER_FAKE", "order_status": "PAID"}}}'
    response = await client.post(
        "/api/v1/payments/cashfree-webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "x-webhook-signature": "FORGED_ATTACKER_SIGNATURE=="
        }
    )
    assert response.status_code == 400
    assert "Invalid webhook signature" in response.json()["detail"]

@pytest.mark.asyncio
async def test_payment_status_never_exposes_password(client):
    """Verifies that checking payment status NEVER returns plaintext passwords."""
    create_res = await client.post("/api/v1/payments/create-order", json={
        "candidateName": "Sneha Roy",
        "email": "sneha.roy@test.com",
        "phone": "9998887776",
        "college": "IIIT Hyderabad",
        "track": "Fullstack Engineering",
        "amount": 4999.00
    })
    order_id = create_res.json()["orderId"]
    
    status_res = await client.get(f"/api/v1/payments/status/{order_id}")
    assert status_res.status_code == 200
    data = status_res.json()
    
    # Critical security assertion: No credentials or password field must exist in payload
    assert "password" not in data
    assert "bitElevateCredentials" not in data
    assert "credentials" not in data
