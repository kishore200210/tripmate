"""
tests/unit/reviews/test_review_service.py

Unit tests for ReviewService.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

import app.db.model_registry  # noqa: F401
from app.core.exceptions import (
    BusinessRuleViolationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from app.modules.destinations.models import Destination, Review
from app.modules.destinations.repository import DestinationRepository
from app.modules.reviews.repository import ReviewRepository
from app.modules.reviews.schemas import (
    ReviewCreateRequest,
    ReviewUpdateRequest,
)
from app.modules.reviews.service import ReviewService
from app.modules.users.enums import UserRole
from app.modules.users.models import User


@pytest.fixture
def mock_review_repository() -> AsyncMock:
    return AsyncMock(spec=ReviewRepository)


@pytest.fixture
def mock_dest_repository() -> AsyncMock:
    return AsyncMock(spec=DestinationRepository)


@pytest.fixture
def review_service(
    mock_review_repository: AsyncMock, mock_dest_repository: AsyncMock
) -> ReviewService:
    return ReviewService(
        repository=mock_review_repository, destination_repository=mock_dest_repository
    )


@pytest.fixture
def sample_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    user.role = UserRole.USER
    return user


@pytest.fixture
def sample_destination() -> Destination:
    dest = Destination()
    dest.id = uuid.uuid4()
    dest.is_deleted = False
    return dest


@pytest.fixture
def sample_review(sample_user: User, sample_destination: Destination) -> Review:
    review = Review()
    review.id = uuid.uuid4()
    review.user_id = sample_user.id
    review.destination_id = sample_destination.id
    review.rating = 5
    review.comment = "Amazing place!"
    review.is_deleted = False
    return review


class TestReviewServiceCreate:
    @pytest.mark.asyncio
    async def test_create_review_success(
        self,
        review_service: ReviewService,
        mock_dest_repository: AsyncMock,
        mock_review_repository: AsyncMock,
        sample_user: User,
        sample_destination: Destination,
        sample_review: Review,
    ) -> None:
        mock_dest_repository.get_by_id.return_value = sample_destination
        mock_review_repository.get_user_review_for_destination.return_value = None
        mock_review_repository.create.return_value = sample_review

        payload = ReviewCreateRequest(rating=5, comment="Amazing place!")

        result = await review_service.create_review(sample_destination.id, payload, sample_user)
        assert result.rating == 5
        assert result.comment == "Amazing place!"
        mock_review_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_duplicate_raises_exception(
        self,
        review_service: ReviewService,
        mock_dest_repository: AsyncMock,
        mock_review_repository: AsyncMock,
        sample_user: User,
        sample_destination: Destination,
        sample_review: Review,
    ) -> None:
        mock_dest_repository.get_by_id.return_value = sample_destination
        # Simulate existing review
        mock_review_repository.get_user_review_for_destination.return_value = sample_review

        payload = ReviewCreateRequest(rating=4, comment="Good place!")

        with pytest.raises(ResourceAlreadyExistsException):
            await review_service.create_review(sample_destination.id, payload, sample_user)


class TestReviewServiceGet:
    @pytest.mark.asyncio
    async def test_get_destination_reviews_success(
        self,
        review_service: ReviewService,
        mock_dest_repository: AsyncMock,
        mock_review_repository: AsyncMock,
        sample_destination: Destination,
        sample_review: Review,
    ) -> None:
        mock_dest_repository.get_by_id.return_value = sample_destination
        mock_review_repository.get_destination_reviews.return_value = ([sample_review], 1)
        mock_review_repository.get_average_rating.return_value = 5.0

        result = await review_service.get_destination_reviews(sample_destination.id)
        assert result.total == 1
        assert result.average_rating == 5.0
        assert result.items[0].rating == 5


class TestReviewServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_review_success(
        self,
        review_service: ReviewService,
        mock_review_repository: AsyncMock,
        sample_user: User,
        sample_review: Review,
    ) -> None:
        mock_review_repository.get_by_id.return_value = sample_review
        mock_review_repository.update.return_value = sample_review

        payload = ReviewUpdateRequest(rating=4)
        result = await review_service.update_review(
            sample_review.id, payload, sample_user
        )

        assert sample_review.rating == 4
        assert result.rating == 4

    @pytest.mark.asyncio
    async def test_update_review_unauthorized_user(
        self,
        review_service: ReviewService,
        mock_review_repository: AsyncMock,
        sample_review: Review,
    ) -> None:
        mock_review_repository.get_by_id.return_value = sample_review
        
        # Different user
        other_user = User()
        other_user.id = uuid.uuid4()

        payload = ReviewUpdateRequest(rating=3)
        with pytest.raises(BusinessRuleViolationException):
            await review_service.update_review(sample_review.id, payload, other_user)


class TestReviewServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_review_success(
        self,
        review_service: ReviewService,
        mock_review_repository: AsyncMock,
        sample_user: User,
        sample_review: Review,
    ) -> None:
        mock_review_repository.get_by_id.return_value = sample_review

        await review_service.delete_review(sample_review.id, sample_user)
        assert sample_review.is_deleted is True
        mock_review_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_review_admin_success(
        self,
        review_service: ReviewService,
        mock_review_repository: AsyncMock,
        sample_review: Review,
    ) -> None:
        mock_review_repository.get_by_id.return_value = sample_review

        admin_user = User()
        admin_user.id = uuid.uuid4()
        admin_user.role = UserRole.ADMIN

        await review_service.delete_review(sample_review.id, admin_user)
        assert sample_review.is_deleted is True
