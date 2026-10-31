import hmac
import hashlib
import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
from passlib.context import CryptContext
from implementation.core.config import settings

# Argon2id password hashing context
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,        # 3 iterations
    argon2__parallelism=4,      # 4 parallel threads
)

def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time verification of password against Argon2id hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Encodes a JWT with claims, expiration, and issuer."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": "cynbit-auth-service"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="cynbit-auth-service"
        )
        return payload
    except (jwt.PyJWTError, ValueError):
        return None

def generate_magic_token() -> Tuple[str, str, datetime]:
    """
    Generates a cryptographically strong single-use onboarding token.
    Returns: (raw_token_for_email, sha256_hash_for_db, expiration_time)
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    return raw_token, token_hash, expires_at

def verify_cashfree_signature(payload_bytes: bytes, signature: str, secret_key: str) -> bool:
    """
    Validates the authenticity of Cashfree Payment Gateway Webhook callbacks
    using HMAC-SHA256 and constant-time string comparison.
    """
    if not signature or not secret_key:
        return False
        
    computed_digest = hmac.new(
        secret_key.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).digest()
    
    computed_signature = base64.b64encode(computed_digest).decode("utf-8")
    return hmac.compare_digest(computed_signature, signature)

