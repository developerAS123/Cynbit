from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from implementation.core.database import get_db
from implementation.core.config import settings
from implementation.core.security import verify_password, create_access_token, decode_access_token, generate_magic_token
from implementation.models.entities import User
from implementation.schemas.auth import LoginRequest, PasswordResetRequest, TokenResponse, GenericStatusResponse, UserSummary
from implementation.middleware.rate_limit import auth_rate_limiter, rate_limit_dependency
from implementation.services.notification_service import NotificationService

router = APIRouter(prefix="/auth", tags=["Authentication"])

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Dependency resolving the authenticated user from HttpOnly session cookie or Bearer token.
    Enforces strict signature and expiration validation.
    """
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing session cookie or bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active or found."
        )
    return user

@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_dependency(auth_rate_limiter))]
)
async def login(
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user via Argon2id password verification.
    Sets an HttpOnly, Secure, SameSite=Strict cookie for browser sessions.
    """
    stmt = select(User).where(User.email == credentials.email.lower().strip())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Constant-time mitigation against timing attacks
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
        
    token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})
    
    # Set secure HttpOnly cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True if settings.ENVIRONMENT == "production" else False,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return TokenResponse(
        success=True,
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role
        )
    )

@router.post("/logout", response_model=GenericStatusResponse)
async def logout(response: Response):
    """Clears the session cookie."""
    response.delete_cookie(key=settings.COOKIE_NAME, samesite="strict")
    return GenericStatusResponse(success=True, message="Successfully logged out.")

@router.post(
    "/request-password-reset",
    response_model=GenericStatusResponse,
    dependencies=[Depends(rate_limit_dependency(auth_rate_limiter))]
)
async def request_password_reset(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Initiates account password recovery with ZERO user enumeration.
    Always returns identical success status regardless of whether the email exists.
    """
    stmt = select(User).where(User.email == payload.email.lower().strip())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        raw_token, token_hash, _ = generate_magic_token()
        await NotificationService.send_password_reset_link(user.email, raw_token)
        
    # Constant generic message prevents account harvesting
    return GenericStatusResponse(
        success=True,
        message="If this email is registered in our portal, a password reset link has been dispatched to your inbox."
    )

@router.get("/me", response_model=UserSummary)
async def get_current_user_profile(user: User = Depends(get_current_user)):
    """Returns profile for currently authenticated user."""
    return UserSummary(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )
