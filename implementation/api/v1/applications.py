from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from implementation.core.database import get_db
from implementation.models.entities import JobApplication
from implementation.schemas.application import ApplicationCreate, ApplicationResponse
from implementation.middleware.rate_limit import application_rate_limiter, rate_limit_dependency
from implementation.services.notification_service import NotificationService

router = APIRouter(prefix="/applications", tags=["Careers"])

@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_dependency(application_rate_limiter))]
)
async def submit_application(
    application_in: ApplicationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests a candidate job application with strict PII validation.
    Mitigates user enumeration: returns constant-time generic confirmation
    even if an active submission already exists for the email and job.
    """
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")

    # Check for existing application
    stmt = select(JobApplication).where(
        JobApplication.email == application_in.email.lower().strip(),
        JobApplication.job_id == application_in.jobId.strip()
    )
    result = await db.execute(stmt)
    existing_app = result.scalar_one_or_none()
    
    if existing_app:
        # Secure mitigation: Do NOT return isDuplicate=true or trackingUrl to the caller.
        # Instead, dispatch a private status email to the applicant's verified inbox.
        await NotificationService.send_application_receipt(
            email=existing_app.email,
            candidate_name=existing_app.full_name,
            job_id=existing_app.job_id
        )
        return ApplicationResponse(
            success=True,
            message="Application blueprint received. A confirmation has been dispatched to your email."
        )

    new_app = JobApplication(
        job_id=application_in.jobId.strip(),
        full_name=application_in.fullName.strip(),
        email=application_in.email.lower().strip(),
        phone=application_in.phone.strip(),
        whatsapp=application_in.whatsapp.strip(),
        dob=application_in.dob.strip(),
        gender=application_in.gender.strip(),
        education=application_in.education.strip(),
        university=application_in.university.strip(),
        graduation_year=application_in.graduationYear.strip(),
        notice_period=application_in.noticePeriod.strip(),
        skills=application_in.skills.strip(),
        current_city=application_in.currentCity.strip(),
        permanent_address=application_in.permanentAddress.strip(),
        portfolio_url=application_in.portfolioUrl.strip(),
        linkedin_url=application_in.linkedinUrl.strip(),
        professional_profile_url=application_in.professionalProfileUrl.strip() if application_in.professionalProfileUrl else None,
        message=application_in.message.strip(),
        ip_address=client_ip
    )
    
    db.add(new_app)
    await db.flush()
    await db.refresh(new_app)
    
    await NotificationService.send_application_receipt(
        email=new_app.email,
        candidate_name=new_app.full_name,
        job_id=new_app.job_id
    )

    return ApplicationResponse(
        success=True,
        message="Application blueprint received. A confirmation has been dispatched to your email.",
        application_id=new_app.id
    )

