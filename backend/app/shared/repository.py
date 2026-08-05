"""
app/shared/repository.py

Generic Base Repository implementing standard CRUD patterns.

Why this exists:
    - Every domain repository (UserRepository, TripRepository) will inherit from this.
    - Enforces a consistent interface across all repositories (LSP).
    - Eliminates duplicated get_by_id / create / update / delete boilerplate (DRY).
    - The Generic[T] type parameter ensures full type safety per model.

Architecture:
    - Repositories receive an AsyncSession via Dependency Injection.
    - Repositories ONLY interact with the database. Zero business logic here.
    - Services receive repositories via their constructors (DI).

Engineering Principles:
    - Generic[T]: Type-safe per-model instantiation.
    - Single Responsibility: Data access ONLY.
    - Open/Closed: Extend via subclassing, never by modifying this base.
"""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository providing standard CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: AsyncSession) -> None:
                super().__init__(model=User, db=db)

            # Add User-specific methods below the base CRUD.
    """

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, record_id: UUID) -> ModelType | None:
        """Fetch a single record by its UUID primary key. Returns None if not found."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[ModelType]:
        """Fetch a paginated list of all records (excluding soft-deleted if applicable)."""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, instance: ModelType) -> ModelType:
        """Persist a new model instance to the database and return it with its ID."""
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """Persist changes to an existing model instance."""
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Permanently delete a record. Prefer soft_delete() for user-facing data."""
        await self.db.delete(instance)
        await self.db.commit()
