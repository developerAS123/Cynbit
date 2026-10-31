from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class InquiryCreate(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=100, description="Contact person full name")
    email: EmailStr = Field(..., description="Business or corporate email address")
    company: Optional[str] = Field(default=None, max_length=150, description="Organization name")
    industry: Optional[str] = Field(default=None, max_length=100, description="Industry sector")
    message: str = Field(..., min_length=10, max_length=3000, description="Project or architectural inquiry message")

class InquiryResponse(BaseModel):
    success: bool
    message: str
    inquiry_id: Optional[str] = None

