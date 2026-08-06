"""
app/modules/users/controller.py

User Controller — thin HTTP translation layer for user operations.
"""

from uuid import UUID

from app.modules.auth.schemas import MessageResponse, UserResponse
from app.modules.users.models import User
from app.modules.users.schemas import (
    AdminUserUpdateRequest,
    PasswordChangeRequest,
    UserPaginatedResponse,
    UserUpdateRequest,
)
from app.modules.users.service import UserService


class UserController:
    """Thin HTTP controller for the Users module."""

    @staticmethod
    async def get_profile(service: UserService, current_user: User) -> UserResponse:
        return await service.get_profile(current_user)

    @staticmethod
    async def update_profile(
        payload: UserUpdateRequest, service: UserService, current_user: User
    ) -> UserResponse:
        return await service.update_profile(current_user, payload)

    @staticmethod
    async def change_password(
        payload: PasswordChangeRequest, service: UserService, current_user: User
    ) -> MessageResponse:
        await service.change_password(current_user, payload)
        return MessageResponse(message="Password updated successfully.")

    @staticmethod
    async def deactivate_account(
        service: UserService, current_user: User
    ) -> MessageResponse:
        await service.deactivate_account(current_user)
        return MessageResponse(message="Account deactivated successfully.")

    # ── Admin Methods ────────────────────────────────────────────────────────

    @staticmethod
    async def admin_list_users(
        skip: int, limit: int, service: UserService
    ) -> UserPaginatedResponse:
        return await service.admin_list_users(skip=skip, limit=limit)

    @staticmethod
    async def admin_get_user(user_id: UUID, service: UserService) -> UserResponse:
        return await service.admin_get_user(user_id)

    @staticmethod
    async def admin_update_user(
        user_id: UUID, payload: AdminUserUpdateRequest, service: UserService
    ) -> UserResponse:
        return await service.admin_update_user(user_id, payload)

    @staticmethod
    async def admin_delete_user(user_id: UUID, service: UserService) -> MessageResponse:
        await service.admin_delete_user(user_id)
        return MessageResponse(message="User account deleted successfully.")
