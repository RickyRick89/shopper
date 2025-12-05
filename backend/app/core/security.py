"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing context - use argon2 instead of bcrypt to avoid 72-byte limit
# or pre-hash long passwords with SHA256 before bcrypt
try:
    # Try to use argon2 if available, otherwise fall back to bcrypt with pre-hashing
    pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
except Exception:
    # Fallback to bcrypt only if argon2 is not available
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    # Pre-hash long passwords before verification
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage.
    
    Uses SHA256 pre-hashing for passwords longer than 72 bytes (bcrypt limit),
    then bcrypt for the final hash.
    """
    # Pre-hash with SHA256 if password is too long for bcrypt
    if len(password.encode('utf-8')) > 72:
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None
