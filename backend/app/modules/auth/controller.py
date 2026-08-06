"""
app/modules/auth/controller.py

Authentication Controller — thin HTTP translation layer.

Architectural Decision — Why a Separate Controller File:
    Many FastAPI tutorials put business logic directly in route handler functions.
    This creates fat route handlers that mix HTTP concerns with business logic.

    We separate:
    - Router (router.py):     Maps URLs + HTTP methods to controller functions.
    - Controller (this file): Receives FastAPI request objects, calls the service,
                               returns HTTP responses. NO business logic here.
    - Service (service.py):   Contains ALL business logic.

    The controller's only job is:
    1. Receive a validated Pydantic schema from the router.
    2. Call the appropriate service method.
    3. Build and return the HTTP response (including headers and cookies).

    This means the controller is completely replaceable — if we switched from
    FastAPI to another framework, only the controller and router would change.
    The service, repository, and models would be untouched.

Architectural Decision — HttpOnly Cookie for Refresh Token:
    Refresh tokens are set as HttpOnly, Secure, SameSite=Lax cookies.
    HttpOnly: JavaScript cannot read the cookie — XSS safe.
    Secure: Only sent over HTTPS in production.
    SameSite=Lax: CSRF protection for browser clients.
    This is a defence-in-depth measure. API clients (mobile apps) use the body value.

Logging in Controllers:
    Controllers log at DEBUG level only — they should not duplicate the
    INFO-level logging already done in the service layer.
"""

import logging

from fastapi import Response
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.modules.auth.service import AuthService

logger = logging.getLogger(__name__)
settings = get_settings()

# Cookie configuration constants
_REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds


class AuthController:
    """
    Thin HTTP controller for the Authentication module.

    Architectural Decision — Controller as a Class:
        Controller methods are grouped into a class for organisation.
        They are NOT bound to the class (no self state) — they're called
        as static-style methods. This mirrors NestJS/Spring controller patterns.
        Each method takes the service as a parameter (injected by the router).
    """

    @staticmethod
    async def register(
        payload: RegisterRequest,
        service: AuthService,
        response: Response,
    ) -> RegisterResponse:
        """
        Handle POST /api/v1/auth/register.

        What the controller does:
            1. Passes the validated payload to the service.
            2. Returns the RegisterResponse as JSON.

        What the controller does NOT do:
            - Hash passwords (service responsibility)
            - Check email uniqueness (service + repository responsibility)
            - Generate tokens (login step, not registration step)

        HTTP Semantics:
            Returns 201 Created (set in the router decorator, not here).
        """
        logger.debug("AuthController.register: delegating to AuthService")
        result = await service.register(payload)
        return result

    @staticmethod
    async def login(
        payload: LoginRequest,
        service: AuthService,
        response: Response,
    ) -> LoginResponse:
        """
        Handle POST /api/v1/auth/login.

        Architectural Decision — Setting the Refresh Token Cookie Here:
            The service generates the refresh token (business concern).
            The controller sets it as an HttpOnly cookie (HTTP concern).
            This is the correct division — the service returns data,
            the controller decides how to deliver it to the client.

        Returns the full LoginResponse in the body AND sets the refresh token
        as a secure cookie for browser clients simultaneously.
        """
        logger.debug("AuthController.login: delegating to AuthService")
        result = await service.login(payload)

        # Set refresh token as HttpOnly cookie for browser clients.
        # API clients (mobile apps) use the refresh_token from the response body.
        response.set_cookie(
            key=_REFRESH_TOKEN_COOKIE_NAME,
            value=result.tokens.refresh_token,
            max_age=_COOKIE_MAX_AGE,
            httponly=True,                                    # Not readable by JavaScript
            secure=settings.APP_ENV == "production",         # HTTPS only in production
            samesite="lax",                                   # CSRF protection
            path="/api/v1/auth/refresh",                      # Scoped to refresh endpoint only
        )

        return result

    @staticmethod
    async def refresh(
        token: str,
        service: AuthService,
    ) -> TokenResponse:
        """
        Handle POST /api/v1/auth/refresh.
        """
        logger.debug("AuthController.refresh: delegating to AuthService")
        return await service.refresh(token)

    @staticmethod
    async def logout(response: Response) -> MessageResponse:
        """
        Handle POST /api/v1/auth/logout.

        Architectural Decision — Stateless JWT Logout:
            JWTs are stateless — there is no server-side session to invalidate.
            'Logout' means:
            1. The client deletes the access token from memory.
            2. We clear the refresh token HttpOnly cookie from the browser.
            3. The access token remains valid until expiry (typically 30 minutes).

            For production systems requiring immediate token invalidation,
            implement a Redis-based token blocklist (Milestone 7 — Rate Limiting).
            For this milestone, short-lived access tokens are the mitigation.

        Why we don't raise an error if not logged in:
            Logout is idempotent — calling it multiple times is safe.
            If the user is already logged out, there's nothing to do.
        """
        logger.debug("AuthController.logout: clearing refresh token cookie")

        # Clear the refresh token cookie by overwriting with an expired cookie.
        response.delete_cookie(
            key=_REFRESH_TOKEN_COOKIE_NAME,
            path="/api/v1/auth/refresh",
        )

        return MessageResponse(message="Logged out successfully.")

    @staticmethod
    async def me(
        service: AuthService,
        token: str,
    ) -> None:
        """
        Handle GET /api/v1/auth/me — returns the currently authenticated user's profile.

        Architectural Decision — /me vs /users/{id}:
            /me is a convenience endpoint that uses the JWT to identify the caller.
            It avoids clients needing to store their own UUID for self-profile access.
            /users/{id} will be implemented in the Users CRUD module (Milestone 2+).
        """
        # Handled directly in router via middleware dependency injection.
        # This method exists for documentation purposes only.
        pass
