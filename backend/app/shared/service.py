"""
app/shared/service.py

Generic Base Service class providing common service infrastructure.

Why this exists:
    - All domain services inherit from this for consistent interface.
    - Reduces boilerplate in individual service classes.
    - Provides a type-safe link between a Service and its primary Repository.

Architecture:
    - Services receive their Repository via constructor injection (DI).
    - Services contain ALL business logic.
    - Services are completely HTTP-agnostic — they raise domain exceptions only.

Engineering Principles:
    - Generic[R]: Type-safe per-repository binding.
    - Single Responsibility: Each service owns one domain's business logic.
    - Dependency Inversion: Services depend on the repository abstraction.
"""

from typing import Generic, TypeVar

from app.shared.repository import BaseRepository

RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)  # type: ignore[type-arg]


class BaseService(Generic[RepositoryType]):
    """
    Generic base service providing a consistent constructor for dependency injection.

    Usage:
        class UserService(BaseService[UserRepository]):
            def __init__(self, repository: UserRepository) -> None:
                super().__init__(repository=repository)

            async def register(self, payload: UserCreateRequest) -> User:
                # Business logic here
                ...
    """

    def __init__(self, repository: RepositoryType) -> None:
        self.repository = repository
