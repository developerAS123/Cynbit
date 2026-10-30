from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from implementation.core.database import get_db
from implementation.models.entities import Inquiry
from implementation.schemas.inquiry import InquiryCreate, InquiryResponse
from implementation.middleware.rate_limit import inquiry_rate_limiter, rate_limit_dependency

router = APIRouter(prefix="/inquiries", tags=["Inquiries"])

@router.post(
    "",
    response_model=InquiryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_dependency(inquiry_rate_limiter))]
)
async def submit_inquiry(
    inquiry_in: InquiryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a business architectural inquiry.
    Protected by sliding-window rate limiting and Pydantic v2 payload sanitization.
    """
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")

    inquiry = Inquiry(
        full_name=inquiry_in.fullName.strip(),
        email=inquiry_in.email.lower().strip(),
        company=inquiry_in.company.strip() if inquiry_in.company else None,
        industry=inquiry_in.industry.strip() if inquiry_in.industry else None,
        message=inquiry_in.message.strip(),
        ip_address=client_ip
    )
    
    db.add(inquiry)
    await db.flush()
    await db.refresh(inquiry)
    
    return InquiryResponse(
        success=True,
        message="Thank you for reaching out. Our engineering architects will contact you shortly.",
        inquiry_id=inquiry.id
    )
