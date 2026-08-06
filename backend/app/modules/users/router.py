"""
app/modules/users/router.py

Users API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import get_current_user, require_role
from app.modules.auth.schemas import MessageResponse, UserResponse
from app.modules.users.controller import UserController
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    AdminUserUpdateRequest,
    PasswordChangeRequest,
    UserPaginatedResponse,
    UserUpdateRequest,
)
from app.modules.users.service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

# ── Dependency Factory ────────────────────────────────────────────────────────

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repository = UserRepository(db=db)
    return UserService(repository=repository)


# ── Current User Profile ──────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await UserController.get_profile(service, current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_profile(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await UserController.update_profile(payload, service, current_user)


@router.put(
    "/me/password",
    response_model=MessageResponse,
    summary="Change password",
)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    return await UserController.change_password(payload, service, current_user)


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Deactivate account",
    description="Soft-deletes the current user's account.",
)
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    return await UserController.deactivate_account(service, current_user)


# ── Admin User Management ─────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=UserPaginatedResponse,
    summary="List users (Admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: UserService = Depends(get_user_service),
) -> UserPaginatedResponse:
    return await UserController.admin_list_users(skip, limit, service)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (Admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def admin_get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await UserController.admin_get_user(user_id, service)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user (Admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def admin_update_user(
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await UserController.admin_update_user(user_id, payload, service)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete user (Admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def admin_delete_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    return await UserController.admin_delete_user(user_id, service)
