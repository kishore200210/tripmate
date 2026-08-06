"""
app/modules/auth/repository.py

Authentication Repository — database access layer for auth operations.

Architectural Decision — Why Auth Has Its Own Repository:
    Auth operations need very specific queries not present in a generic CRUD repo:
        - get_by_email(): Used on every login — the most critical auth query.
        - get_active_by_email(): Combines email + is_active filter — used for login.
        - create_user(): Creates user with pre-hashed password.
    Placing these in a shared BaseRepository would pollute it with domain-specific logic.
    The auth repository EXTENDS BaseRepository — it inherits all CRUD and adds auth queries.

Architectural Decision — Repository Contract:
    1. Repositories ONLY talk to the database.
    2. They NEVER call security functions (no hashing, no JWT here).
    3. They NEVER raise HTTP exceptions — only return None or the model.
    4. Services decide what to do with None (raise ResourceNotFoundException, etc.).

This strict separation means repositories are independently testable without
any knowledge of HTTP, JWT, or business rules.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class AuthRepository(BaseRepository[User]):
    """
    Repository for auth-specific database queries on the User table.

    Inherits from BaseRepository[User] which provides:
        - get_by_id(id)
        - create(instance)
        - update(instance)
        - delete(instance)

    Adds auth-specific queries:
        - get_by_email(email)
        - get_active_by_email(email)
        - email_exists(email)
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Dependency Injection Constructor.

        Architectural Decision — DI via Constructor:
            The AsyncSession is injected via the constructor, not imported globally.
            This means:
            1. Tests can inject a mock or test session easily.
            2. Each HTTP request gets a fresh session (no shared state between requests).
            3. The repository doesn't know how the session was created — pure DI.
        """
        super().__init__(model=User, db=db)

    async def get_by_email(self, email: str) -> User | None:
        """
        Fetch a user by email address regardless of active/deleted status.

        Architectural Decision — Return None, not raise:
            Repositories return None when not found.
            The SERVICE layer decides whether None → 401, 404, or retry.
            This keeps HTTP semantics OUT of the repository.

        Args:
            email: The email address to look up (case-insensitive via ilike).

        Returns:
            User ORM instance or None if not found.
        """
        logger.debug("AuthRepository.get_by_email: querying email=%s", email)
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_active_by_email(self, email: str) -> User | None:
        """
        Fetch an active, non-deleted user by email.

        Used for login: both is_active and is_deleted are checked at DB level.
        This is more efficient than fetching first and checking in Python.

        Architectural Decision — Filter at DB Level:
            Filtering in the WHERE clause is always faster than fetching
            and checking in Python, especially under load. The database
            uses the email index + is_deleted index effectively here.

        Args:
            email: The email address to look up.

        Returns:
            Active User ORM instance or None.
        """
        logger.debug("AuthRepository.get_active_by_email: querying email=%s", email)
        result = await self.db.execute(
            select(User).where(
                User.email == email.lower().strip(),
                User.is_active.is_(True),
                User.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """
        Check whether an email is already registered.

        Architectural Decision — Dedicated exists() query:
            Using SELECT 1 ... LIMIT 1 is faster than fetching the full User row
            just to check existence. Important for high-volume registration endpoints.

        Args:
            email: The email address to check.

        Returns:
            True if the email is already in use, False otherwise.
        """
        result = await self.db.execute(
            select(User.id).where(
                User.email == email.lower().strip(),
                User.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_user(
        self,
        name: str,
        email: str,
        password_hash: str,
    ) -> User:
        """
        Create and persist a new User record.

        Architectural Decision — Repository Creates the ORM Instance:
            The Service passes validated, processed data (already hashed password).
            The Repository creates the ORM object and handles persistence.
            This means the Service never imports the User model directly —
            it only calls repository methods. Clean dependency direction.

        Args:
            name: User's display name.
            email: User's email address (stored lowercase).
            password_hash: Pre-computed Argon2id hash — NEVER plain text.

        Returns:
            Persisted User instance with database-assigned id and timestamps.
        """
        logger.info("AuthRepository.create_user: creating user email=%s", email)
        user = User(
            id=uuid.uuid4(),
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=password_hash,
        )
        return await self.create(user)
