"""
app/modules/auth/router.py

Authentication API Router — URL mapping and Swagger documentation.

Architectural Decision — Router's Sole Responsibilities:
    1. Map HTTP methods + paths to controller functions.
    2. Declare request/response schemas for FastAPI (Swagger/OpenAPI generation).
    3. Inject service dependencies via Depends().
    4. Set HTTP status codes.

    The router does NOT:
    - Contain business logic (that's the service)
    - Handle exceptions directly (global handlers in main.py do that)
    - Access the database (that's the repository)

Architectural Decision — OpenAPI Tags and Swagger Integration:
    All routes use tags=["Authentication"] so they appear grouped in Swagger UI.
    Every endpoint has a detailed summary and description for Swagger.
    response_model ensures FastAPI generates the correct OpenAPI response schema
    AND automatically filters out any extra fields (like password_hash) from ORM objects.

Architectural Decision — API Versioning via Prefix:
    All routes are prefixed with /api/v1/auth.
    The /api prefix separates API routes from static assets.
    The /v1 prefix allows non-breaking v2 introduction in the future.
    The /auth prefix scopes all authentication operations.

Endpoints:
    POST   /api/v1/auth/register   Register new account
    POST   /api/v1/auth/login      Login and get tokens
    POST   /api/v1/auth/refresh    Refresh access token
    POST   /api/v1/auth/logout     Logout and clear cookie
    GET    /api/v1/auth/me         Get current user profile
"""

import logging

from fastapi import APIRouter, Depends, Response, status, Cookie, HTTPException

from app.modules.auth.controller import AuthController
from app.modules.auth.middleware import get_auth_service, get_current_user
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ── POST /register ────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="""
Create a new TripMate user account.

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Notes:**
- Email must be unique across the platform.
- The account is created with the `user` role by default.
- Passwords are hashed with **Argon2id** before storage. Plain-text passwords are never stored.
- After registration, call `/auth/login` to obtain tokens.
    """,
    responses={
        201: {"description": "Account created successfully."},
        409: {"description": "Email address is already registered."},
        422: {"description": "Validation error — check password complexity or email format."},
    },
)
async def register(
    payload: RegisterRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """
    Architectural Decision — Route Handler as Pure Delegation:
        This function receives the validated payload from FastAPI,
        injects the service via Depends(), and delegates EVERYTHING to the controller.
        Route handlers should be ≤5 lines. Any more means logic crept in.
    """
    logger.debug("POST /auth/register invoked")
    return await AuthController.register(payload, service, response)


# ── POST /login ───────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and obtain JWT tokens",
    description="""
Authenticate with email and password.

**Returns:**
- `access_token`: Short-lived JWT (30 minutes). Store in memory — NOT localStorage.
- `refresh_token`: Long-lived JWT (7 days). Also set as an **HttpOnly cookie** for browser clients.
- `user`: The authenticated user profile.

**Security Notes:**
- Error messages are intentionally vague to prevent email enumeration.
- Both incorrect email and incorrect password return the same 401 response.
- Refresh token is set as `HttpOnly; Secure; SameSite=Lax` cookie for browsers.
    """,
    responses={
        200: {"description": "Login successful. Tokens returned."},
        401: {"description": "Invalid credentials (email or password incorrect)."},
        422: {"description": "Validation error — malformed email or missing fields."},
    },
)
async def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    logger.debug("POST /auth/login invoked")
    return await AuthController.login(payload, service, response)


# ── POST /refresh ─────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh the access token",
    description="""
Exchange a valid refresh token for a new access token.

**When to call this:**
- When the access token has expired (HTTP 401 response on a protected endpoint).
- Proactively before expiry using the `expires_in` value from login.

**Notes:**
- The refresh token must be of type `refresh` — access tokens are rejected.
- The same refresh token is returned (not rotated on every call).
- If the refresh token has expired, the user must log in again.
    """,
    responses={
        200: {"description": "New access token issued successfully."},
        401: {"description": "Refresh token is expired or the account has been deactivated."},
        422: {"description": "Token is malformed or wrong type."},
    },
)
async def refresh(
    payload: RefreshTokenRequest | None = None,
    refresh_token: str | None = Cookie(None),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    logger.debug("POST /auth/refresh invoked")
    
    token = refresh_token or (payload.refresh_token if payload else None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token is missing from body and cookies."
        )
        
    return await AuthController.refresh(token, service)


# ── POST /logout ──────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and clear session",
    description="""
Logout the current user.

**What this does:**
- Clears the `refresh_token` HttpOnly cookie from the browser.
- Instructs the client to delete the access token from memory.

**What this does NOT do:**
- Immediately invalidate the JWT access token (JWTs are stateless).
- The access token remains technically valid until its 30-minute expiry.

**For immediate token invalidation** (high-security scenarios),
a Redis token blocklist will be implemented in a future milestone.

This endpoint does NOT require authentication — it is safe to call even when not logged in.
    """,
    responses={
        200: {"description": "Logged out successfully."},
    },
)
async def logout(
    response: Response,
) -> MessageResponse:
    logger.debug("POST /auth/logout invoked")
    return await AuthController.logout(response)


# ── GET /me ───────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the current authenticated user's profile",
    description="""
Returns the profile of the currently authenticated user based on the provided JWT.

**Authentication Required:** `Authorization: Bearer <access_token>`

**Returns:**
- User ID, name, email, role, and active status.

**Notes:**
- Sensitive fields (password_hash, is_deleted, etc.) are NEVER included in the response.
- This is a convenience endpoint — the user's ID is derived from the JWT, not a URL parameter.
    """,
    responses={
        200: {"description": "Current user profile returned."},
        401: {"description": "Access token missing, invalid, or expired."},
    },
)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Architectural Decision — /me Handled Entirely in Router:
        This is the one route where the controller is bypassed.
        The get_current_user dependency already handles authentication and DB fetch.
        The route just converts the User ORM to a UserResponse schema.
        No service call needed — no business logic involved.
    """
    logger.debug("GET /auth/me invoked for user id=%s", current_user.id)
    return UserResponse.model_validate(current_user)
