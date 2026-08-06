"""
app/modules/auth/middleware.py

FastAPI authentication and authorization dependencies.

Architectural Decision — Dependencies, Not True Middleware:
    These are FastAPI Depends() functions, not ASGI middleware (like CORSMiddleware).
    True ASGI middleware runs on EVERY request unconditionally.
    FastAPI Depends() is applied per-route — only routes that need auth get it.
    This means public routes (health check, register, login) are completely unaffected
    and don't pay the cost of JWT validation.

    Trade-off: True middleware is simpler for "all routes must be auth'd".
    FastAPI Depends is better for mixed public/private routing, which we have.

Architectural Decision — get_auth_service() as a Dependency:
    The service is constructed fresh per request via Depends().
    This ensures each request gets its OWN repository, which gets its OWN
    database session. No shared mutable state between requests.
    This is the correct pattern for async FastAPI applications.

Architectural Decision — RBAC via require_role() Factory:
    Instead of decorating routes with a fixed `admin_only` dependency,
    we use a factory function `require_role(UserRole.ADMIN)` that RETURNS
    a dependency. This is more flexible — any combination of roles can be
    required per route without duplicating code.

    Example:
        # Any authenticated user:
        @router.get("/trips", dependencies=[Depends(get_current_user)])

        # Admin only:
        @router.get("/admin/stats", dependencies=[Depends(require_role(UserRole.ADMIN))])

Usage:
    from app.modules.auth.middleware import get_current_user, require_role
    from app.modules.users.enums import UserRole

    @router.get("/protected")
    async def protected(user: User = Depends(get_current_user)):
        return {"user_id": str(user.id)}

    @router.delete("/admin/user/{id}")
    async def admin_delete(user: User = Depends(require_role(UserRole.ADMIN))):
        ...
"""

import logging
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthorizationException, InvalidTokenException
from app.db.session import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Bearer Token Extractor ────────────────────────────────────────────────────
# HTTPBearer extracts the JWT from "Authorization: Bearer <token>" header.
# auto_error=False means we raise our OWN exception (not FastAPI's default 403).
# This gives us full control over the error response format.
_bearer_scheme = HTTPBearer(auto_error=False)


# ── Service Factory Dependency ────────────────────────────────────────────────

def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """
    FastAPI dependency that constructs and returns an AuthService.

    Architectural Decision — Dependency Chain:
        get_db() → AuthRepository(db) → AuthService(repository)

        FastAPI resolves this chain automatically:
        1. get_db() yields a fresh AsyncSession for this request.
        2. AuthRepository is constructed with that session.
        3. AuthService is constructed with that repository.

        This means each HTTP request gets completely fresh, isolated instances
        of the session, repository, and service. No shared state, no bugs.

    Why NOT use global singletons:
        Global singletons share database sessions across requests,
        which causes race conditions and data corruption in async code.
    """
    repository = AuthRepository(db=db)
    return AuthService(repository=repository)


# ── Authentication Dependency ─────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    FastAPI dependency: extracts JWT, validates it, and returns the current user.

    Architectural Decision — Who Does What:
        - _bearer_scheme: Extracts the token from the Authorization header (HTTP concern).
        - auth_service.get_current_user(): Validates the token and fetches the user (business concern).
        - This function: Bridges the two layers. Thin orchestration only.

    Architectural Decision — Manual Bearer Extraction vs OAuth2PasswordBearer:
        FastAPI's OAuth2PasswordBearer is simpler but hardcodes the token URL
        and always returns 401 with WWW-Authenticate header on failure.
        HTTPBearer with auto_error=False gives us full control over error responses,
        which is necessary to match our standard error format:
            {"error": {"message": "...", "detail": "..."}}

    Args:
        credentials: Extracted Bearer token from the Authorization header.
        auth_service: Injected AuthService instance.

    Returns:
        The authenticated User ORM object.

    Raises:
        InvalidTokenException → caught by global handler → HTTP 401.
        AuthenticationException → caught by global handler → HTTP 401.
    """
    if credentials is None:
        logger.warning("get_current_user: no Authorization header provided")
        raise InvalidTokenException(
            message="Authentication required.",
            detail="No Authorization header found. Include 'Authorization: Bearer <token>'.",
        )

    user = await auth_service.get_current_user(credentials.credentials)
    logger.debug("get_current_user: authenticated user id=%s role=%s", user.id, user.role.value)
    return user


# ── Optional Authentication Dependency ───────────────────────────────────────

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User | None:
    """
    Like get_current_user but returns None instead of raising if no token is present.

    Use this for routes that behave differently for authenticated vs anonymous users
    (e.g., public destination list — authenticated users see personalised results).

    Args:
        credentials: Optional Bearer token from Authorization header.
        auth_service: Injected AuthService.

    Returns:
        The User if authenticated, None if no token provided.

    Raises:
        InvalidTokenException: Only if a token IS provided but is invalid.
        (Anonymous access = no token at all = returns None, not an error.)
    """
    if credentials is None:
        return None
    return await auth_service.get_current_user(credentials.credentials)


# ── RBAC Authorization Dependency Factory ────────────────────────────────────

def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory for Role-Based Access Control.

    Architectural Decision — Factory Pattern for RBAC:
        Returns a FastAPI-compatible async dependency function.
        The factory captures the required roles in a closure.
        The returned dependency runs AFTER get_current_user succeeds.

        This means RBAC is a two-step process:
            1. get_current_user: Is this a valid, active user? (AuthN)
            2. require_role():   Does this user have the required role? (AuthZ)
        These two concerns are separated — Authentication before Authorization.

    Args:
        *allowed_roles: One or more UserRole values that are permitted.

    Returns:
        A FastAPI dependency function that enforces RBAC.

    Usage:
        @router.delete("/admin/users/{id}")
        async def admin_delete(user: User = Depends(require_role(UserRole.ADMIN))):
            ...

        # Multiple roles allowed:
        @router.get("/reports")
        async def reports(user: User = Depends(require_role(UserRole.ADMIN, UserRole.USER))):
            ...
    """

    async def _rbac_check(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """
        RBAC enforcement: checks the authenticated user's role against allowed roles.

        Raises:
            AuthorizationException → caught by global handler → HTTP 403.
        """
        if current_user.role not in allowed_roles:
            logger.warning(
                "RBAC denied: user id=%s role=%s attempted access requiring roles=%s",
                current_user.id,
                current_user.role.value,
                [r.value for r in allowed_roles],
            )
            raise AuthorizationException(
                message="Access denied.",
                detail=(
                    f"This action requires one of the following roles: "
                    f"{', '.join(r.value for r in allowed_roles)}. "
                    f"Your role is '{current_user.role.value}'."
                ),
            )
        return current_user

    return _rbac_check
