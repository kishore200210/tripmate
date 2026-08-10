"""
app/modules/analytics/router.py

HTTP Routing Layer — Analytics Module.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import require_role
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.analytics.service import AnalyticsService
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.schemas import DashboardAnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    """FastAPI dependency factory yielding a configured AnalyticsService."""
    repository = AnalyticsRepository(db=db)
    return AnalyticsService(repository=repository)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=DashboardAnalyticsResponse,
    summary="Get site-wide admin analytics dashboard statistics",
)
async def get_dashboard_analytics(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    service: AnalyticsService = Depends(get_analytics_service),
) -> DashboardAnalyticsResponse:
    """
    Returns site-wide aggregations, including user metrics, trip status breakdowns,
    popular destinations, and registration/trip-creation monthly trend lists.
    Only accessible by authenticated users with the ADMIN role.
    """
    return await service.get_dashboard_analytics()
