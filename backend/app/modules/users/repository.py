"""
app/modules/users/repository.py

User Repository — database access layer for user operations.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """
    Repository for user-specific database queries.
    Inherits standard CRUD operations from BaseRepository.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=User, db=db)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by email (case-insensitive)."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def count_all(self, include_deleted: bool = False) -> int:
        """Count total users for pagination metadata."""
        query = select(func.count(User.id))
        if not include_deleted:
            query = query.where(User.is_deleted.is_(False))
        result = await self.db.execute(query)
        return result.scalar_one() or 0
