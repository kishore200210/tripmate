"""
app/modules/auth/service.py

Authentication Service — all authentication business logic.

Architectural Decision — Why the Service Layer Exists:
    The Service is the brain of the module. It:
    1. Orchestrates repository calls (data access).
    2. Calls security utilities (hashing, JWT creation).
    3. Enforces business rules (e.g., cannot login if deactivated).
    4. Raises DOMAIN exceptions (not HTTP exceptions).
    5. Is completely HTTP-agnostic — it knows nothing about requests or responses.

    This means the AuthService can be used:
    - In a FastAPI HTTP handler (current use)
    - In a background task
    - In a CLI script
    - In a test — without any HTTP infrastructure

Architectural Decision — Service Receives Repository via DI:
    AuthService.__init__(repository: AuthRepository)
    The service does NOT create the repository — it receives it.
    This means tests can inject a mock repository without touching the database.
    This is the Dependency Inversion Principle in action.

Architectural Decision — Constant-Time Password Comparison:
    We ALWAYS call verify_password() even when the user doesn't exist.
    If we returned early on "user not found", an attacker could measure
    the response time to enumerate valid email addresses (timing attack).
    By always running the hash comparison, all invalid login attempts
    take the same amount of time.
"""

import logging
from uuid import UUID

from app.core.exceptions import (
    AuthenticationException,
    InvalidTokenException,
    ResourceAlreadyExistsException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.config import get_settings
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    TokenPayload,
    TokenResponse,
    UserResponse,
)
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)
settings = get_settings()

# A deliberately invalid hash used during timing-attack-resistant login.
# When a user is not found, we compare the supplied password against this
# dummy hash so the response time is indistinguishable from a real failed login.
_DUMMY_HASH = hash_password("dummy_timing_attack_prevention_password")


class AuthService(BaseService[AuthRepository]):
    """
    Service class containing all authentication business logic.

    Inherits from BaseService[AuthRepository] which provides:
        self.repository: AuthRepository

    Public Methods:
        register(payload) -> RegisterResponse
        login(payload)    -> LoginResponse
        refresh(token)    -> TokenResponse
        logout()          -> dict (stateless — just instruction to client)
        get_current_user(token) -> User (used by middleware)
    """

    def __init__(self, repository: AuthRepository) -> None:
        super().__init__(repository=repository)

    # ── Register ─────────────────────────────────────────────────────────────

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        """
        Register a new user account.

        Business Rules:
            1. Email must be unique (checked at DB level via repository).
            2. Password is hashed with Argon2id before storage.
            3. The plain-text password is NEVER stored, logged, or returned.
            4. Role is always 'user' at registration — admin access is granted separately.

        Architectural Decision — Hash in Service, Not Repository:
            The repository receives an already-hashed password.
            This means the repository is completely unaware of security operations.
            The service is the only layer that knows about password hashing.

        Args:
            payload: Validated RegisterRequest schema.

        Returns:
            RegisterResponse containing the new UserResponse.

        Raises:
            ResourceAlreadyExistsException: If email is already registered.
        """
        logger.info("AuthService.register: attempting registration email=%s", payload.email)

        # 1. Check email uniqueness (DB-level, race-condition safe via UNIQUE constraint)
        if await self.repository.email_exists(payload.email):
            logger.warning("AuthService.register: duplicate email=%s", payload.email)
            raise ResourceAlreadyExistsException(
                message="An account with this email address already exists.",
                detail=f"Email '{payload.email}' is already registered.",
            )

        # 2. Hash password with Argon2id — NEVER store plain text
        password_hash = hash_password(payload.password)
        logger.debug("AuthService.register: password hashed successfully")

        # 3. Persist the new user
        user = await self.repository.create_user(
            name=payload.name,
            email=payload.email,
            password_hash=password_hash,
        )
        logger.info(
            "AuthService.register: user created successfully id=%s email=%s",
            user.id,
            user.email,
        )

        return RegisterResponse(
            user=UserResponse.model_validate(user),
            message="Registration successful. Please log in.",
        )

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, payload: LoginRequest) -> LoginResponse:
        """
        Authenticate a user and issue JWT access + refresh tokens.

        Business Rules:
            1. Email must exist and the account must be active and not soft-deleted.
            2. Password must match the stored Argon2id hash.
            3. Timing-attack mitigation: always run verify_password(), even if user not found.
            4. Tokens are generated only after all checks pass.

        Architectural Decision — Intentionally Vague Error Messages:
            We return "Invalid credentials" for BOTH wrong email AND wrong password.
            If we returned different messages, an attacker could enumerate valid emails.
            This is a deliberate security decision, not poor UX.

        Args:
            payload: Validated LoginRequest schema.

        Returns:
            LoginResponse containing user data + access + refresh tokens.

        Raises:
            AuthenticationException: For any invalid credential scenario.
        """
        logger.info("AuthService.login: login attempt email=%s", payload.email)

        # 1. Fetch the user — includes is_active + is_deleted check at DB level
        user = await self.repository.get_active_by_email(payload.email)

        # 2. Timing-attack-resistant password check
        #    If user is None, we still call verify_password with a dummy hash.
        #    This makes all failed logins take the same amount of time.
        hash_to_check = user.password_hash if user is not None else _DUMMY_HASH
        password_valid = verify_password(payload.password, hash_to_check)

        if user is None or not password_valid:
            logger.warning(
                "AuthService.login: failed login attempt email=%s (user_found=%s)",
                payload.email,
                user is not None,
            )
            # Intentionally vague — do not reveal whether email exists
            raise AuthenticationException(
                message="Invalid credentials.",
                detail="Email or password is incorrect.",
            )

        logger.info(
            "AuthService.login: login successful id=%s email=%s role=%s",
            user.id,
            user.email,
            user.role.value,
        )

        # 3. Generate tokens
        tokens = self._generate_tokens(user)

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Issue a new access token using a valid refresh token.

        Architectural Decision — Refresh Token Validation Strategy:
            We validate the refresh token using the same JWT decode machinery.
            The token payload MUST contain 'type': 'refresh' to be accepted.
            An access token passed as a refresh token is explicitly rejected.
            This prevents access token reuse for refresh — a known attack vector.

        Args:
            refresh_token: A valid JWT refresh token string.

        Returns:
            TokenResponse with new access token (refresh token is re-used).

        Raises:
            InvalidTokenException: If token is expired, malformed, or wrong type.
            AuthenticationException: If the user no longer exists or is deactivated.
        """
        logger.info("AuthService.refresh: refresh token exchange requested")

        # 1. Decode and validate the refresh token
        try:
            payload_dict = decode_access_token(refresh_token)
        except InvalidTokenException:
            logger.warning("AuthService.refresh: invalid or expired refresh token")
            raise

        # 2. Enforce type='refresh' — reject access tokens used as refresh tokens
        if payload_dict.get("type") != "refresh":
            logger.warning("AuthService.refresh: access token used as refresh token — rejected")
            raise InvalidTokenException(
                message="Invalid token type.",
                detail="An access token cannot be used to refresh. Provide a refresh token.",
            )

        # 3. Verify the user still exists and is active
        user_id = UUID(payload_dict["sub"])
        user = await self.repository.get_by_id(user_id)

        if user is None or not user.is_active or user.is_deleted:
            logger.warning(
                "AuthService.refresh: user not found or deactivated id=%s", user_id
            )
            raise AuthenticationException(
                message="Account not found or has been deactivated.",
                detail="The user associated with this token no longer exists.",
            )

        logger.info("AuthService.refresh: token refreshed for user id=%s", user.id)

        # 4. Issue a new access token (refresh token is reused — not rotated here)
        new_access_token = create_access_token(user.id, user.role.value)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,  # Reuse existing refresh token
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── Get Current User (used by Middleware) ────────────────────────────────

    async def get_current_user(self, token: str) -> User:
        """
        Validate a JWT access token and return the associated User.

        Architectural Decision — Why This Is in the Service, Not Middleware:
            The middleware CALLS this method — it doesn't implement the logic.
            The middleware is responsible for EXTRACTING the token from the header.
            The service is responsible for VALIDATING the token and FETCHING the user.
            This keeps the middleware thin (HTTP concern) and the service testable.

        Args:
            token: Raw JWT access token string from Authorization header.

        Returns:
            The active User ORM object.

        Raises:
            InvalidTokenException: If token is malformed or expired.
            AuthenticationException: If the user no longer exists or is deactivated.
        """
        # 1. Decode the JWT
        try:
            payload_dict = decode_access_token(token)
        except InvalidTokenException:
            raise

        # 2. Parse into a typed schema (catches malformed payloads)
        try:
            token_payload = TokenPayload(**payload_dict)
        except Exception as e:
            raise InvalidTokenException(
                message="Token payload is malformed.",
                detail=str(e),
            ) from e

        # 3. Reject refresh tokens used as access tokens
        if token_payload.type == "refresh":
            raise InvalidTokenException(
                message="Invalid token type.",
                detail="A refresh token cannot be used to authenticate requests.",
            )

        # 4. Fetch the user from the database to confirm they still exist
        user = await self.repository.get_by_id(token_payload.sub)

        if user is None or not user.is_active or user.is_deleted:
            raise AuthenticationException(
                message="Account not found or has been deactivated.",
                detail="The user associated with this token no longer exists.",
            )

        return user

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _generate_tokens(self, user: User) -> TokenResponse:
        """
        Generate a complete access + refresh token pair for a user.

        Architectural Decision — Private Helper:
            Both login() and (future) social auth flows need token generation.
            Extracting it into a private method avoids code duplication (DRY)
            while keeping it internal to the service (not exposed to callers).
        """
        access_token = create_access_token(user.id, user.role.value)
        refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
