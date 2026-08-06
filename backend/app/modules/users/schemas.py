"""
app/modules/users/schemas.py

Pydantic v2 schemas for the Users module.

Architecture:
    - Defines the API contract for user profile management and admin user operations.
    - Uses field validators for data sanitization and business rules (e.g., password complexity).
"""

import re
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.auth.schemas import UserResponse
from app.modules.users.enums import UserRole

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic pagination response schema."""
    items: list[T]
    total: int
    skip: int
    limit: int


class UserUpdateRequest(BaseModel):
    """
    Schema for PATCH /api/v1/users/me (User updating their own profile).
    All fields are optional because it's a PATCH request.
    """
    name: str | None = Field(
        None, min_length=2, max_length=100, description="User's display name."
    )
    email: EmailStr | None = Field(
        None, description="User's email address."
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            if re.search(r"[<>\"';&]", v):
                raise ValueError("Name contains invalid characters.")
            return v.strip()
        return v


class PasswordChangeRequest(BaseModel):
    """Schema for PUT /api/v1/users/me/password."""
    current_password: str = Field(..., description="The user's current password.")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="The new password.",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class AdminUserUpdateRequest(BaseModel):
    """
    Schema for PATCH /api/v1/users/{id} (Admin updating any user).
    Admins can change roles and active status.
    """
    name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = Field(None)
    role: UserRole | None = Field(None, description="Change user role (e.g., promote to admin).")
    is_active: bool | None = Field(None, description="Deactivate or reactivate user.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            if re.search(r"[<>\"';&]", v):
                raise ValueError("Name contains invalid characters.")
            return v.strip()
        return v


class UserPaginatedResponse(PaginatedResponse[UserResponse]):
    """Response schema for GET /api/v1/users."""
    pass
