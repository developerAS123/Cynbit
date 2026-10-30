import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Numeric, Index
from implementation.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="intern", nullable=False)  # intern, mentor, admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    company = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    status = Column(String(50), default="NEW", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(100), index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    phone = Column(String(50), nullable=False)
    whatsapp = Column(String(50), nullable=False)
    dob = Column(String(50), nullable=False)
    gender = Column(String(50), nullable=False)
    education = Column(String(255), nullable=False)
    university = Column(String(255), nullable=False)
    graduation_year = Column(String(20), nullable=False)
    notice_period = Column(String(50), nullable=False)
    skills = Column(String(500), nullable=False)
    current_city = Column(String(100), nullable=False)
    permanent_address = Column(Text, nullable=False)
    portfolio_url = Column(String(500), nullable=False)
    linkedin_url = Column(String(500), nullable=False)
    professional_profile_url = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_app_email_job", "email", "job_id"),
    )

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), index=True, nullable=False)
    customer_phone = Column(String(50), nullable=False)
    track = Column(String(100), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="ACTIVE", index=True, nullable=False)  # ACTIVE, PAID, FAILED, CANCELLED
    payment_session_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor = Column(String(255), nullable=False)  # User ID, IP, or 'ANONYMOUS'
    action = Column(String(100), nullable=False)  # LOGIN, ORDER_CREATE, INQUIRY_SUBMIT
    resource = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    status_code = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
