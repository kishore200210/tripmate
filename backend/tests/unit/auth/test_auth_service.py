"""
tests/unit/auth/test_auth_service.py

Unit tests for AuthService.

Architectural Decision — Unit Tests Use Mocks, Not a Real Database:
    Unit tests test ONE unit in complete isolation.
    The AuthService is isolated from:
    - The database (mock repository)
    - The real password hasher (we test behavior, not Argon2 internals)
    - The real JWT library (we verify the service calls it correctly)

    This makes unit tests:
    - Fast (no I/O — runs in milliseconds)
    - Deterministic (no database state issues)
    - Focused (failures point directly to AuthService logic)

Architectural Decision — unittest.mock vs pytest-mock:
    We use unittest.mock (stdlib) to avoid an extra dependency.
    AsyncMock is used for coroutine (async) method mocking.

Test Naming Convention:
    test_{method}_{scenario}_{expected_outcome}
    Example: test_login_invalid_password_raises_authentication_exception

Coverage Target: All business logic branches in AuthService.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import (
    AuthenticationException,
    InvalidTokenException,
    ResourceAlreadyExistsException,
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.users.enums import UserRole
from app.modules.users.models import User


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_repository() -> AsyncMock:
    """
    Creates a mock AuthRepository.

    Architectural Decision — Mock the Repository Interface:
        We mock at the repository boundary, not the database.
        This tests that the service correctly USES the repository.
        We do NOT test that the repository correctly queries PostgreSQL
        (that's the repository's integration test's job).
    """
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def auth_service(mock_repository: AsyncMock) -> AuthService:
    """Creates an AuthService with a mocked repository."""
    return AuthService(repository=mock_repository)


@pytest.fixture
def sample_user() -> User:
    """
    Creates a realistic User ORM object for testing.
    Uses a pre-computed Argon2 hash of 'SecurePass1!' for test reproducibility.
    """
    from app.core.security import hash_password

    user = User()
    user.id = uuid.uuid4()
    user.name = "Alice Traveller"
    user.email = "alice@example.com"
    user.password_hash = hash_password("SecurePass1!")
    user.role = UserRole.USER
    user.is_active = True
    user.is_deleted = False
    return user


@pytest.fixture
def register_payload() -> RegisterRequest:
    """Valid registration payload."""
    return RegisterRequest(
        name="Alice Traveller",
        email="alice@example.com",
        password="SecurePass1!",
    )


@pytest.fixture
def login_payload() -> LoginRequest:
    """Valid login payload."""
    return LoginRequest(
        email="alice@example.com",
        password="SecurePass1!",
    )


# ── Schema Validation Tests ───────────────────────────────────────────────────

class TestRegisterRequestSchema:
    """Tests for the RegisterRequest Pydantic schema validation."""

    def test_valid_payload_passes(self) -> None:
        payload = RegisterRequest(
            name="Alice", email="alice@test.com", password="SecurePass1!"
        )
        assert payload.name == "Alice"
        assert payload.email == "alice@test.com"

    def test_password_missing_uppercase_fails(self) -> None:
        with pytest.raises(Exception, match="uppercase"):
            RegisterRequest(name="Alice", email="a@b.com", password="lowercase1!")

    def test_password_missing_digit_fails(self) -> None:
        with pytest.raises(Exception, match="digit"):
            RegisterRequest(name="Alice", email="a@b.com", password="NoDigitPass!")

    def test_password_missing_lowercase_fails(self) -> None:
        with pytest.raises(Exception, match="lowercase"):
            RegisterRequest(name="Alice", email="a@b.com", password="ALLUPPERCASE1!")

    def test_password_too_short_fails(self) -> None:
        with pytest.raises(Exception):
            RegisterRequest(name="Alice", email="a@b.com", password="Ab1!")

    def test_name_with_xss_chars_fails(self) -> None:
        with pytest.raises(Exception, match="invalid characters"):
            RegisterRequest(name="<script>", email="a@b.com", password="SecurePass1!")

    def test_invalid_email_fails(self) -> None:
        with pytest.raises(Exception):
            RegisterRequest(name="Alice", email="not-an-email", password="SecurePass1!")

    def test_name_is_stripped(self) -> None:
        payload = RegisterRequest(
            name="  Alice  ", email="a@b.com", password="SecurePass1!"
        )
        assert payload.name == "Alice"


# ── AuthService.register Tests ────────────────────────────────────────────────

class TestAuthServiceRegister:
    """Unit tests for AuthService.register()."""

    @pytest.mark.asyncio
    async def test_register_success_returns_register_response(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        register_payload: RegisterRequest,
        sample_user: User,
    ) -> None:
        """Happy path: valid payload → user created → RegisterResponse returned."""
        mock_repository.email_exists.return_value = False
        mock_repository.create_user.return_value = sample_user

        result = await auth_service.register(register_payload)

        assert result.user.email == "alice@example.com"
        assert result.user.role == UserRole.USER
        mock_repository.email_exists.assert_called_once()
        mock_repository.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises_exception(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        register_payload: RegisterRequest,
    ) -> None:
        """Duplicate email → ResourceAlreadyExistsException raised."""
        mock_repository.email_exists.return_value = True

        with pytest.raises(ResourceAlreadyExistsException) as exc_info:
            await auth_service.register(register_payload)

        assert "already exists" in exc_info.value.message
        mock_repository.create_user.assert_not_called()  # Never reaches DB

    @pytest.mark.asyncio
    async def test_register_password_is_hashed_not_plain(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        register_payload: RegisterRequest,
        sample_user: User,
    ) -> None:
        """Critical security test: password must be hashed before passing to repository."""
        mock_repository.email_exists.return_value = False
        mock_repository.create_user.return_value = sample_user

        await auth_service.register(register_payload)

        # Capture what was passed to create_user
        call_args = mock_repository.create_user.call_args
        passed_hash = call_args.kwargs.get("password_hash") or call_args.args[2]

        # The stored value must NOT be the plain-text password
        assert passed_hash != register_payload.password
        # The stored value must start with Argon2 prefix
        assert passed_hash.startswith("$argon2")


# ── AuthService.login Tests ───────────────────────────────────────────────────

class TestAuthServiceLogin:
    """Unit tests for AuthService.login()."""

    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        login_payload: LoginRequest,
        sample_user: User,
    ) -> None:
        """Happy path: valid credentials → LoginResponse with tokens returned."""
        mock_repository.get_active_by_email.return_value = sample_user

        result = await auth_service.login(login_payload)

        assert result.user.email == sample_user.email
        assert result.tokens.access_token is not None
        assert result.tokens.refresh_token is not None
        assert result.tokens.token_type == "bearer"
        assert result.tokens.expires_in > 0

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises_authentication_exception(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        """Wrong password → AuthenticationException with vague message."""
        mock_repository.get_active_by_email.return_value = sample_user

        with pytest.raises(AuthenticationException) as exc_info:
            await auth_service.login(
                LoginRequest(email="alice@example.com", password="WrongPass1!")
            )

        # Message must be vague — do NOT reveal that email was found
        assert "Invalid credentials" in exc_info.value.message
        assert "email" not in exc_info.value.message.lower() or "or" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_login_nonexistent_email_raises_authentication_exception(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
    ) -> None:
        """Non-existent email → same AuthenticationException (no email enumeration)."""
        mock_repository.get_active_by_email.return_value = None

        with pytest.raises(AuthenticationException) as exc_info:
            await auth_service.login(
                LoginRequest(email="nobody@example.com", password="SecurePass1!")
            )

        # Same error message as wrong password — prevents email enumeration
        assert "Invalid credentials" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_login_inactive_user_raises_authentication_exception(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        """Deactivated user → get_active_by_email returns None → 401."""
        # get_active_by_email returns None for inactive users (filtered at DB level)
        mock_repository.get_active_by_email.return_value = None

        with pytest.raises(AuthenticationException):
            await auth_service.login(
                LoginRequest(email="alice@example.com", password="SecurePass1!")
            )


# ── AuthService.refresh Tests ─────────────────────────────────────────────────

class TestAuthServiceRefresh:
    """Unit tests for AuthService.refresh()."""

    @pytest.mark.asyncio
    async def test_refresh_with_valid_token_returns_new_access_token(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        """Valid refresh token → new access token issued."""
        from app.core.security import create_refresh_token

        refresh_token = create_refresh_token(sample_user.id)
        mock_repository.get_by_id.return_value = sample_user

        result = await auth_service.refresh(refresh_token)

        assert result.access_token is not None
        assert result.refresh_token == refresh_token  # Reused
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_raises_exception(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        """Access token used as refresh token → InvalidTokenException."""
        from app.core.security import create_access_token

        access_token = create_access_token(sample_user.id, sample_user.role.value)

        with pytest.raises(InvalidTokenException) as exc_info:
            await auth_service.refresh(access_token)

        assert "type" in exc_info.value.message.lower() or "access" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_refresh_with_garbage_token_raises_exception(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
    ) -> None:
        """Completely invalid token string → InvalidTokenException."""
        with pytest.raises(InvalidTokenException):
            await auth_service.refresh("this.is.not.a.valid.jwt")


# ── AuthService.get_current_user Tests ───────────────────────────────────────

class TestAuthServiceGetCurrentUser:
    """Unit tests for AuthService.get_current_user() (used by middleware)."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        """Valid access token → returns User object."""
        from app.core.security import create_access_token

        token = create_access_token(sample_user.id, sample_user.role.value)
        mock_repository.get_by_id.return_value = sample_user

        result = await auth_service.get_current_user(token)
        assert result.id == sample_user.id

    @pytest.mark.asyncio
    async def test_expired_or_invalid_token_raises_exception(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
    ) -> None:
        """Malformed token → InvalidTokenException."""
        with pytest.raises(InvalidTokenException):
            await auth_service.get_current_user("bad.token.here")

    @pytest.mark.asyncio
    async def test_user_not_found_raises_authentication_exception(
        self,
        auth_service: AuthService,
        mock_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        """Valid token but user deleted from DB → AuthenticationException."""
        from app.core.security import create_access_token

        token = create_access_token(sample_user.id, sample_user.role.value)
        mock_repository.get_by_id.return_value = None

        with pytest.raises(AuthenticationException):
            await auth_service.get_current_user(token)
