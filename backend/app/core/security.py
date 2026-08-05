"""
app/core/security.py

Authentication and authorisation utilities.

Technologies:
    - python-jose: JWT creation and verification (approved stack).
    - pwdlib[argon2]: Argon2id password hashing (approved stack).

Architecture:
    - This module is a UTILITY layer. It contains NO business logic.
    - JWT functions are called by the auth Service and auth Middleware.
    - Password functions are called by the User Service ONLY.
    - Never import this module directly in Routers or Controllers.

Engineering Principles:
    - Single Responsibility: This file ONLY handles cryptographic operations.
    - Open/Closed: New token types can be added without modifying existing functions.

Security Notes:
    - Tokens use HS256 algorithm with a server-side SECRET_KEY.
    - Argon2id is memory-hard and the current OWASP-recommended algorithm.
    - Token payloads are minimal (user_id + role only — no PII).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenException

settings = get_settings()

# ── Password Hashing ─────────────────────────────────────
# Argon2id: memory-hard, GPU-resistant, PHC winner.
_password_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using Argon2id.

    Args:
        plain_password: The raw password from the registration form.

    Returns:
        The Argon2 hash string — safe to store in the database.

    Important:
        NEVER log or return the plain_password. Call this in the Service layer.
    """
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored Argon2 hash.

    Args:
        plain_password: The raw password from the login form.
        hashed_password: The Argon2 hash from the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return _password_hasher.verify(plain_password, hashed_password)


# ── JWT Token Generation ──────────────────────────────────

def create_access_token(user_id: UUID, role: str) -> str:
    """
    Generate a signed JWT access token.

    Args:
        user_id: The UUID of the authenticated user.
        role: The user's RBAC role (e.g. "user" or "admin").

    Returns:
        A signed JWT string to be sent to the client.

    Token Payload:
        - sub: User UUID as string (standard JWT subject claim).
        - role: RBAC role for authorization middleware.
        - exp: Expiry timestamp (UTC).
        - iat: Issued-at timestamp (UTC).
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """
    Generate a signed JWT refresh token with a longer TTL.

    Args:
        user_id: The UUID of the authenticated user.

    Returns:
        A signed refresh JWT string. Store this securely (HttpOnly cookie).
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Args:
        token: The raw JWT string from the Authorization header.

    Returns:
        The decoded token payload dict.

    Raises:
        InvalidTokenException: If the token is expired, malformed, or signature is invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise InvalidTokenException(
            message="Token is invalid or has expired.",
            detail=str(e),
        ) from e
