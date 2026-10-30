from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class ApplicationCreate(BaseModel):
    jobId: str = Field(..., min_length=2, max_length=100, description="Role slug identifier")
    fullName: str = Field(..., min_length=2, max_length=150, description="Full applicant name")
    email: EmailStr = Field(..., description="Applicant personal email")
    phone: str = Field(..., min_length=8, max_length=20, description="Primary contact phone number")
    whatsapp: str = Field(..., min_length=8, max_length=20, description="WhatsApp contact number")
    dob: str = Field(..., min_length=8, max_length=20, description="Date of birth YYYY-MM-DD")
    gender: str = Field(..., min_length=2, max_length=50, description="Gender identity")
    education: str = Field(..., min_length=2, max_length=200, description="Highest qualification summary")
    university: str = Field(..., min_length=2, max_length=200, description="College or university name")
    graduationYear: str = Field(..., min_length=4, max_length=10, description="Year of graduation")
    noticePeriod: str = Field(..., min_length=1, max_length=50, description="Notice period / availability")
    skills: str = Field(..., min_length=2, max_length=500, description="Key technical competencies")
    currentCity: str = Field(..., min_length=2, max_length=100, description="Current city of residence")
    permanentAddress: str = Field(..., min_length=5, max_length=500, description="Full residential address")
    portfolioUrl: str = Field(..., min_length=5, max_length=500, description="Drive or web portfolio link")
    linkedinUrl: str = Field(..., min_length=5, max_length=500, description="LinkedIn profile URL")
    professionalProfileUrl: Optional[str] = Field(default=None, max_length=500, description="GitHub / GitLab URL")
    message: str = Field(..., min_length=10, max_length=3000, description="Statement of purpose / motivation")
    agreedToTerms: bool = Field(..., description="Consent checkbox")

class ApplicationResponse(BaseModel):
    success: bool
    message: str
    application_id: Optional[str] = None
