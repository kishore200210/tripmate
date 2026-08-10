"""
app/modules/analytics/schemas.py

Pydantic v2 schemas for the Analytics module.
"""

from pydantic import BaseModel, Field


class SummaryMetrics(BaseModel):
    """Overall summary counts and aggregates."""
    total_users: int = Field(..., description="Total registered users (excluding soft-deleted)")
    active_users: int = Field(..., description="Active users (excluding soft-deleted)")
    total_trips: int = Field(..., description="Total trips planned (excluding soft-deleted)")
    completed_trips: int = Field(..., description="Completed trips (excluding soft-deleted)")
    average_trip_budget: float | None = Field(None, description="Average budget across non-deleted trips with budgets")
    total_trip_budget: float | None = Field(None, description="Total budget across all non-deleted trips")


class StatusDistribution(BaseModel):
    """Breakdown of trips by their current status."""
    planning: int = Field(0, description="Count of trips in planning status")
    confirmed: int = Field(0, description="Count of trips in confirmed status")
    ongoing: int = Field(0, description="Count of trips in ongoing status")
    completed: int = Field(0, description="Count of trips in completed status")
    cancelled: int = Field(0, description="Count of trips in cancelled status")


class TopDestination(BaseModel):
    """Most popular travel destination in trips."""
    name: str = Field(..., description="Destination name or geocoded place name")
    country: str = Field(..., description="Destination country or geocoded country")
    trip_count: int = Field(..., description="Number of trips to this destination")


class MonthlyTrend(BaseModel):
    """Monthly count of registrations or trip creations."""
    month: str = Field(..., description="Year and month in YYYY-MM format")
    count: int = Field(..., description="Count of entities created in this month")


class DashboardAnalyticsResponse(BaseModel):
    """Consolidated dashboard analytics response."""
    summary: SummaryMetrics
    status_distribution: StatusDistribution
    top_destinations: list[TopDestination]
    monthly_user_registrations: list[MonthlyTrend]
    monthly_trip_creations: list[MonthlyTrend]
