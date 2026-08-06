"""
tests/unit/users/test_user_service.py

Unit tests for UserService.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

# Import model registry to ensure all SQLAlchemy models are known to the mapper
import app.db.model_registry  # noqa: F401

from app.core.exceptions import (
    AuthenticationException,
    BusinessRuleViolationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    AdminUserUpdateRequest,
    PasswordChangeRequest,
    UserUpdateRequest,
)
from app.modules.users.service import UserService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_repository: AsyncMock) -> UserService:
    return UserService(repository=mock_repository)


@pytest.fixture
def sample_user() -> User:
    from app.core.security import hash_password

    user = User()
    user.id = uuid.uuid4()
    user.name = "Alice"
    user.email = "alice@example.com"
    user.password_hash = hash_password("OldPass1!")
    user.role = UserRole.USER
    user.is_active = True
    user.is_deleted = False
    return user


class TestUserServiceProfile:
    @pytest.mark.asyncio
    async def test_get_profile_returns_user_response(
        self, user_service: UserService, sample_user: User
    ) -> None:
        result = await user_service.get_profile(sample_user)
        assert result.id == sample_user.id
        assert result.email == "alice@example.com"

    @pytest.mark.asyncio
    async def test_update_profile_success(
        self, user_service: UserService, mock_repository: AsyncMock, sample_user: User
    ) -> None:
        payload = UserUpdateRequest(name="Alice Updated", email="alice.new@example.com")
        mock_repository.get_by_email.return_value = None
        mock_repository.update.return_value = sample_user  # In real life, it updates the object in place

        result = await user_service.update_profile(sample_user, payload)
        
        assert sample_user.name == "Alice Updated"
        assert sample_user.email == "alice.new@example.com"
        mock_repository.update.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_email_raises_exception(
        self, user_service: UserService, mock_repository: AsyncMock, sample_user: User
    ) -> None:
        payload = UserUpdateRequest(email="bob@example.com")
        other_user = User(id=uuid.uuid4(), email="bob@example.com")
        mock_repository.get_by_email.return_value = other_user

        with pytest.raises(ResourceAlreadyExistsException):
            await user_service.update_profile(sample_user, payload)


class TestUserServicePassword:
    @pytest.mark.asyncio
    async def test_change_password_success(
        self, user_service: UserService, mock_repository: AsyncMock, sample_user: User
    ) -> None:
        payload = PasswordChangeRequest(
            current_password="OldPass1!", new_password="NewPass2!"
        )
        
        await user_service.change_password(sample_user, payload)
        
        from app.core.security import verify_password
        assert verify_password("NewPass2!", sample_user.password_hash)
        mock_repository.update.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_raises_exception(
        self, user_service: UserService, mock_repository: AsyncMock, sample_user: User
    ) -> None:
        payload = PasswordChangeRequest(
            current_password="WrongPass!", new_password="NewPass2!"
        )
        
        with pytest.raises(AuthenticationException):
            await user_service.change_password(sample_user, payload)


class TestUserServiceDeactivate:
    @pytest.mark.asyncio
    async def test_deactivate_account_success(
        self, user_service: UserService, mock_repository: AsyncMock, sample_user: User
    ) -> None:
        await user_service.deactivate_account(sample_user)
        assert sample_user.is_deleted is True
        assert sample_user.is_active is False
        mock_repository.update.assert_called_once_with(sample_user)


class TestUserServiceAdmin:
    @pytest.mark.asyncio
    async def test_admin_list_users(
        self, user_service: UserService, mock_repository: AsyncMock, sample_user: User
    ) -> None:
        mock_repository.get_all.return_value = [sample_user]
        mock_repository.count_all.return_value = 1

        result = await user_service.admin_list_users(skip=0, limit=10)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == sample_user.id

    @pytest.mark.asyncio
    async def test_admin_delete_user_success(
        self, user_service: UserService, mock_repository: AsyncMock, sample_user: User
    ) -> None:
        mock_repository.get_by_id.return_value = sample_user

        await user_service.admin_delete_user(sample_user.id)
        
        assert sample_user.is_deleted is True
        mock_repository.update.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_admin_delete_admin_raises_exception(
        self, user_service: UserService, mock_repository: AsyncMock, sample_user: User
    ) -> None:
        sample_user.role = UserRole.ADMIN
        mock_repository.get_by_id.return_value = sample_user

        with pytest.raises(BusinessRuleViolationException):
            await user_service.admin_delete_user(sample_user.id)
