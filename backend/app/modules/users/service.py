"""
app/modules/users/service.py

User Service — business logic for user management.
"""

import logging
from uuid import UUID

from app.core.exceptions import (
    AuthenticationException,
    BusinessRuleViolationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from app.core.security import hash_password, verify_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    AdminUserUpdateRequest,
    PasswordChangeRequest,
    UserPaginatedResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.shared.service import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService[UserRepository]):
    """Service layer for user operations."""

    def __init__(self, repository: UserRepository) -> None:
        super().__init__(repository=repository)

    async def get_profile(self, current_user: User) -> UserResponse:
        """Get the current user's profile."""
        return UserResponse.model_validate(current_user)

    async def update_profile(
        self, current_user: User, payload: UserUpdateRequest
    ) -> UserResponse:
        """Update the current user's profile details."""
        logger.info("UserService.update_profile: user id=%s", current_user.id)

        if payload.email and payload.email.lower() != current_user.email:
            existing = await self.repository.get_by_email(payload.email)
            if existing and existing.id != current_user.id:
                raise ResourceAlreadyExistsException(
                    message="Email address already in use.",
                    detail="Please choose a different email address.",
                )
            current_user.email = payload.email.lower()

        if payload.name:
            current_user.name = payload.name

        updated_user = await self.repository.update(current_user)
        return UserResponse.model_validate(updated_user)

    async def change_password(
        self, current_user: User, payload: PasswordChangeRequest
    ) -> None:
        """Change the user's password."""
        logger.info("UserService.change_password: user id=%s", current_user.id)

        if not verify_password(payload.current_password, current_user.password_hash):
            raise AuthenticationException(
                message="Current password is incorrect.",
            )

        current_user.password_hash = hash_password(payload.new_password)
        await self.repository.update(current_user)

    async def deactivate_account(self, current_user: User) -> None:
        """Soft-delete the current user's account."""
        logger.info("UserService.deactivate_account: user id=%s", current_user.id)
        current_user.soft_delete()
        current_user.is_active = False
        await self.repository.update(current_user)

    # ── Admin Methods ────────────────────────────────────────────────────────

    async def admin_list_users(
        self, skip: int = 0, limit: int = 20
    ) -> UserPaginatedResponse:
        """List all users (Admin only)."""
        logger.info("UserService.admin_list_users: skip=%d limit=%d", skip, limit)
        users = await self.repository.get_all(skip=skip, limit=limit)
        total = await self.repository.count_all(include_deleted=False)

        items = [UserResponse.model_validate(u) for u in users if not u.is_deleted]

        return UserPaginatedResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    async def admin_get_user(self, user_id: UUID) -> UserResponse:
        """Get any user by ID (Admin only)."""
        user = await self.repository.get_by_id(user_id)
        if not user or user.is_deleted:
            raise ResourceNotFoundException("User not found.")
        return UserResponse.model_validate(user)

    async def admin_update_user(
        self, user_id: UUID, payload: AdminUserUpdateRequest
    ) -> UserResponse:
        """Update any user's profile or status (Admin only)."""
        logger.info("UserService.admin_update_user: target id=%s", user_id)
        user = await self.repository.get_by_id(user_id)
        if not user or user.is_deleted:
            raise ResourceNotFoundException("User not found.")

        if payload.email and payload.email.lower() != user.email:
            existing = await self.repository.get_by_email(payload.email)
            if existing and existing.id != user.id:
                raise ResourceAlreadyExistsException(
                    message="Email address already in use."
                )
            user.email = payload.email.lower()

        if payload.name:
            user.name = payload.name
        if payload.role:
            user.role = payload.role
        if payload.is_active is not None:
            user.is_active = payload.is_active

        updated_user = await self.repository.update(user)
        return UserResponse.model_validate(updated_user)

    async def admin_delete_user(self, user_id: UUID) -> None:
        """Soft-delete a user account (Admin only)."""
        logger.info("UserService.admin_delete_user: target id=%s", user_id)
        user = await self.repository.get_by_id(user_id)
        if not user or user.is_deleted:
            raise ResourceNotFoundException("User not found.")
        
        if user.role.value == "admin":
            raise BusinessRuleViolationException(
                "Cannot delete an admin account. Demote to user first."
            )

        user.soft_delete()
        user.is_active = False
        await self.repository.update(user)
