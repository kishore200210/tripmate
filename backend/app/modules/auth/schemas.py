"""
app/modules/auth/schemas.py

Pydantic v2 schemas for the Authentication module.

Architectural Decision — Why Schemas are Separate from Models:
    SQLAlchemy models represent the DATABASE shape.
    Pydantic schemas represent the API CONTRACT shape.
    They are intentionally different:
        - The API NEVER exposes password_hash, is_deleted, or internal timestamps.
        - The API enforces additional validation rules (password complexity, email format)
          that are API concerns, not database concerns.
    This separation is the core of the MVC Contract Layer.

Schema Naming Convention (enforced project-wide):
    - Request schemas end in  ...Request  (what the client sends IN)
    - Response schemas end in ...Response (what the server sends OUT)
    - Internal schemas end in ...Schema   (used between service layers)

Pydantic Best Practices Applied:
    - model_config = ConfigDict(from_attributes=True): enables ORM → schema conversion.
    - Field() with description: powers Swagger documentation automatically.
    - @field_validator: business-level validation beyond type checking.
    - Passwords are NEVER included in any Response schema.

Security Notes:
    - Passwords must be at least 8 chars with complexity enforced at schema level.
    - Tokens are returned in the body (access) and cookie (refresh) — NOT logged.
    - The UserResponse schema deliberately omits all security-sensitive fields.
"""

import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.users.enums import UserRole


# ── Request Schemas ────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """
    Schema for POST /api/v1/auth/register.

    Architectural Decision — Validation at Schema Layer:
        Password complexity is enforced HERE, not in the service.
        The service layer should receive an already-validated payload.
        This keeps the service focused on business logic (registration flow),
        not input sanitisation. This follows the Single Responsibility Principle.
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name. Between 2 and 100 characters.",
        examples=["Alice Traveller"],
    )
    email: EmailStr = Field(
        ...,
        description="A valid, unique email address used for login.",
        examples=["alice@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must contain uppercase, lowercase, and digit).",
        examples=["SecurePass1!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Enforce OWASP minimum password complexity.

        Architectural Decision — Why validate here, not in the service:
            Pydantic validators run before the service is even called.
            This provides fast, cheap rejection with a clear 422 error,
            before any database I/O occurs.

        Rules:
            - At least one uppercase letter
            - At least one lowercase letter
            - At least one digit
        """
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("name")
    @classmethod
    def validate_name_no_special_chars(cls, v: str) -> str:
        """Prevent XSS injection via name field — names should be plain text."""
        if re.search(r"[<>\"';&]", v):
            raise ValueError("Name contains invalid characters.")
        return v.strip()


class LoginRequest(BaseModel):
    """
    Schema for POST /api/v1/auth/login.

    Architectural Decision — Intentionally Simple:
        Login only needs email + password. No extra validation needed —
        the service handles incorrect credential logic (wrong password → 401).
    """

    email: EmailStr = Field(
        ...,
        description="Registered email address.",
        examples=["alice@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Account password.",
        examples=["SecurePass1!"],
    )


class RefreshTokenRequest(BaseModel):
    """
    Schema for POST /api/v1/auth/refresh.

    Architectural Decision — Token in Body vs Cookie:
        Refresh tokens CAN be in HttpOnly cookies (more secure, immune to XSS).
        We also accept them in the request body for API client compatibility.
        The middleware layer handles both. The schema handles body delivery.
    """

    refresh_token: str = Field(
        ...,
        description="A valid JWT refresh token issued at login.",
    )


# ── Response Schemas ───────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """
    Safe user representation for API responses.

    Architectural Decision — What We EXCLUDE:
        - password_hash: NEVER exposed via API. Ever.
        - is_deleted: Internal soft-delete flag — not a client concern.
        - deleted_at: Internal audit field.
        - created_at / updated_at: Excluded from auth responses (may be added to profile endpoints).

    The from_attributes=True config allows direct ORM model → schema conversion:
        user_schema = UserResponse.model_validate(user_orm_object)
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="User's unique identifier (UUID v4).")
    name: str = Field(description="User's display name.")
    email: str = Field(description="User's email address.")
    role: UserRole = Field(description="User's RBAC role (user | admin).")
    is_active: bool = Field(description="Whether the account is currently active.")


class TokenResponse(BaseModel):
    """
    Response schema for successful login and token refresh.

    Architectural Decision — Access vs Refresh Token Delivery:
        - access_token: Short-lived (30 min). Returned in response BODY.
          The client stores this in memory (NOT localStorage — XSS risk).
        - refresh_token: Long-lived (7 days). Returned in response BODY here,
          but the router also sets it as an HttpOnly cookie for browser clients.
          API clients (mobile apps) use the body value.
        - token_type: Always "bearer" — required by OAuth2 spec.

    Why we include expires_in:
        Clients can use this to schedule token refresh proactively,
        without needing to inspect the JWT payload.
    """

    access_token: str = Field(description="Short-lived JWT access token (30 minutes).")
    refresh_token: str = Field(description="Long-lived JWT refresh token (7 days).")
    token_type: str = Field(default="bearer", description="Token type — always 'bearer'.")
    expires_in: int = Field(description="Access token lifetime in seconds.")


class RegisterResponse(BaseModel):
    """Response for a successful registration."""

    user: UserResponse
    message: str = Field(default="Registration successful. Please log in.")


class LoginResponse(BaseModel):
    """
    Response for a successful login.

    Architectural Decision — Why Return Both User and Tokens:
        The frontend needs the user object immediately after login
        to populate the UI (name, role, avatar). Without it, the client
        would need to make a second GET /me request immediately after login.
        Returning both in one response avoids that round-trip.
    """

    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    """Generic message-only response (used for logout, password change, etc.)."""

    message: str


# ── Internal Schemas ───────────────────────────────────────────────────────────


class TokenPayload(BaseModel):
    """
    Internal schema representing a decoded JWT payload.

    Architectural Decision — Why Parse JWT Payload into a Pydantic Model:
        Raw JWT payloads are untyped dicts. Parsing them into a Pydantic model:
        1. Provides full type safety (sub: UUID, role: UserRole).
        2. Makes middleware code self-documenting.
        3. Catches malformed token payloads at decode time with a clear error.

    This is used ONLY in the auth middleware — never sent over the wire.
    """

    sub: UUID = Field(description="User UUID from the JWT 'sub' claim.")
    role: UserRole = Field(description="User role from the JWT 'role' claim.")
    type: str = Field(default="access", description="Token type: 'access' or 'refresh'.")
