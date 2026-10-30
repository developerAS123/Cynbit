import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from implementation.core.database import get_db
from implementation.models.entities import Order, User
from implementation.schemas.payment import OrderCreateRequest, OrderResponse, PaymentVerificationResponse
from implementation.services.payment_service import PaymentService
from implementation.services.notification_service import NotificationService
from implementation.core.security import generate_magic_token, hash_password
from implementation.middleware.rate_limit import payment_rate_limiter, rate_limit_dependency

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post(
    "/create-order",
    response_model=OrderResponse,
    dependencies=[Depends(rate_limit_dependency(payment_rate_limiter))]
)
async def create_payment_order(
    order_in: OrderCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a merchant payment session with Cashfree Payments.
    Stores pending order state in the relational database.
    """
    cf_data = await PaymentService.create_order(order_in)
    
    order = Order(
        order_id=cf_data["order_id"],
        customer_name=order_in.candidateName.strip(),
        customer_email=order_in.email.lower().strip(),
        customer_phone=order_in.phone.strip(),
        track=order_in.track.strip(),
        amount=order_in.amount,
        status="ACTIVE",
        payment_session_id=cf_data["payment_session_id"]
    )
    db.add(order)
    await db.flush()
    
    return OrderResponse(
        success=True,
        orderId=order.order_id,
        paymentSessionId=order.payment_session_id,
        environment=cf_data["environment"],
        message="Payment session initialized."
    )

@router.post("/cashfree-webhook", status_code=status.HTTP_200_OK)
async def handle_cashfree_webhook(
    request: Request,
    x_webhook_signature: str = Header(None, alias="x-webhook-signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Asynchronous Webhook Ingestion Engine for Cashfree payment reconciliation.
    Cryptographically validates HMAC-SHA256 signature before mutating order states.
    Fulfills candidate account creation via secure magic links without plaintext passwords.
    """
    body_bytes = await request.body()
    
    # Cryptographic signature validation
    if not x_webhook_signature or not PaymentService.verify_webhook(body_bytes, x_webhook_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature."
        )
        
    payload = await request.json()
    order_info = payload.get("data", {}).get("order", {})
    order_id = order_info.get("order_id")
    order_status = order_info.get("order_status")
    
    if not order_id:
        return {"status": "ignored", "reason": "Missing order_id in webhook data"}
        
    stmt = select(Order).where(Order.order_id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    
    if not order:
        return {"status": "ignored", "reason": "Order not found in database"}
        
    # Idempotent state transition
    if order_status == "PAID" and order.status != "PAID":
        order.status = "PAID"
        
        # Zero-Trust Candidate Provisioning:
        # Check if user account exists or provision new account with temporary high-entropy hash
        user_stmt = select(User).where(User.email == order.customer_email)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        
        raw_token, token_hash, _ = generate_magic_token()
        
        if not user:
            # Create user account with a secure placeholder hash; candidate sets their own password
            placeholder_hash = hash_password(uuid.uuid4().hex + uuid.uuid4().hex)
            new_user = User(
                email=order.customer_email,
                hashed_password=placeholder_hash,
                full_name=order.customer_name,
                role="intern",
                is_active=True
            )
            db.add(new_user)
            await db.flush()
            
        # Dispatch magic onboarding link to candidate's email
        await NotificationService.send_onboarding_magic_link(
            email=order.customer_email,
            candidate_name=order.customer_name,
            magic_token=raw_token
        )
        
    return {"status": "success", "order_id": order_id, "current_status": order.status}

@router.get("/status/{order_id}", response_model=PaymentVerificationResponse)
async def check_order_status(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Queries settlement state for an order.
    CRITICAL: Never exposes plaintext passwords or sensitive credentials!
    """
    stmt = select(Order).where(Order.order_id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )
        
    message = (
        "Payment successfully settled. Onboarding instructions have been dispatched to your email."
        if order.status == "PAID"
        else f"Order status is currently {order.status}."
    )
    
    return PaymentVerificationResponse(
        success=(order.status == "PAID"),
        orderId=order.order_id,
        status=order.status,
        message=message
    )
