from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class OrderCreateRequest(BaseModel):
    candidateName: str = Field(..., min_length=2, max_length=150, description="Enrolling candidate name")
    email: EmailStr = Field(..., description="Candidate contact email")
    phone: str = Field(..., min_length=10, max_length=20, description="Candidate contact phone number")
    college: str = Field(..., min_length=2, max_length=150, description="College / Institution")
    track: str = Field(..., min_length=2, max_length=100, description="Program track (e.g., Backend, AI)")
    amount: float = Field(default=4999.00, gt=0, description="Order fee in INR")

class OrderResponse(BaseModel):
    success: bool
    orderId: str
    paymentSessionId: str
    environment: str
    message: str

class CashfreeWebhookData(BaseModel):
    order: Dict[str, Any]
    payment: Optional[Dict[str, Any]] = None
    customer_details: Optional[Dict[str, Any]] = None

class CashfreeWebhookPayload(BaseModel):
    data: CashfreeWebhookData
    event_time: str
    type: str

class PaymentVerificationResponse(BaseModel):
    success: bool
    orderId: str
    status: str
    message: str
