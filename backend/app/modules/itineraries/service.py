"""
app/modules/itineraries/service.py

Itinerary Service — business logic for itinerary management.
"""

import logging
import uuid
from uuid import UUID

from app.core.exceptions import ResourceNotFoundException
from app.modules.itineraries.repository import ItineraryRepository
from app.modules.itineraries.schemas import (
    ItineraryItemCreateRequest,
    ItineraryItemResponse,
    ItineraryItemUpdateRequest,
    TimelineResponse,
    ItineraryResponse,
    DayPlanResponse,
    AIGenerateRequest,
)
from app.modules.trips.models import ItineraryItem, Itinerary, DayPlan
from app.modules.ai_concierge.itinerary_generator import ItineraryGenerator
from sqlalchemy import select, delete
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)


class ItineraryService(BaseService[ItineraryRepository]):
    """Service layer for itinerary operations."""

    def __init__(
        self, repository: ItineraryRepository, trip_repository: TripRepository
    ) -> None:
        super().__init__(repository=repository)
        self.trip_repository = trip_repository

    async def _verify_trip_ownership(self, trip_id: UUID, user_id: UUID) -> None:
        """Helper to ensure a trip exists and is owned by the user."""
        trip = await self.trip_repository.get_user_trip(trip_id=trip_id, user_id=user_id)
        if not trip:
            raise ResourceNotFoundException("Trip not found.")

    async def get_timeline(self, trip_id: UUID, current_user: User) -> TimelineResponse:
        """Fetch the full itinerary timeline for a trip, ensuring ownership."""
        await self._verify_trip_ownership(trip_id, current_user.id)
        
        items = await self.repository.get_trip_timeline(trip_id)
        response_items = [ItineraryItemResponse.model_validate(item) for item in items]
        
        return TimelineResponse(
            trip_id=trip_id,
            items=response_items,
            total_items=len(response_items)
        )

    async def get_ai_itinerary(self, trip_id: UUID, current_user: User) -> ItineraryResponse | None:
        """Fetch the AI itinerary metadata and day plans."""
        await self._verify_trip_ownership(trip_id, current_user.id)
        
        stmt = select(Itinerary).where(Itinerary.trip_id == trip_id, Itinerary.is_deleted.is_(False))
        result = await self.repository.db.execute(stmt)
        itinerary = result.scalar_one_or_none()
        
        if not itinerary:
            return None
            
        day_plans_stmt = select(DayPlan).where(DayPlan.itinerary_id == itinerary.id, DayPlan.is_deleted.is_(False)).order_by(DayPlan.day_no)
        day_plans_result = await self.repository.db.execute(day_plans_stmt)
        day_plans = list(day_plans_result.scalars().all())
        
        return ItineraryResponse(
            id=itinerary.id,
            trip_id=itinerary.trip_id,
            budget_estimate=itinerary.budget_estimate,
            packing_checklist=itinerary.packing_checklist,
            restaurant_recommendations=itinerary.restaurant_recommendations,
            local_attractions=itinerary.local_attractions,
            weather_suggestions=itinerary.weather_suggestions,
            day_plans=[DayPlanResponse.model_validate(dp) for dp in day_plans]
        )

    async def generate_full_itinerary(self, trip_id: UUID, payload: AIGenerateRequest, current_user: User) -> ItineraryResponse:
        await self._verify_trip_ownership(trip_id, current_user.id)
        trip = await self.trip_repository.get_user_trip(trip_id=trip_id, user_id=current_user.id)
        
        # Calculate duration
        duration_days = 3 # default
        if trip.start_date and trip.end_date:
            duration_days = (trip.end_date - trip.start_date).days + 1
            
        destination_name = "your custom destination"
        if trip.destination_id:
            # We would typically fetch destination, but let's just use trip title as fallback for now
            # Assume destination is part of the title or we can load it. For simplicity, pass title
            destination_name = trip.title
            
        generator = ItineraryGenerator()
        ai_data = await generator.generate_itinerary(destination_name, duration_days, payload.preferences)
        
        # Delete existing Itinerary, DayPlans, and ItineraryItems for this trip
        await self.repository.db.execute(delete(ItineraryItem).where(ItineraryItem.trip_id == trip_id))
        await self.repository.db.execute(delete(Itinerary).where(Itinerary.trip_id == trip_id))
        
        # Create new Itinerary
        import json
        itinerary = Itinerary(
            id=uuid.uuid4(),
            trip_id=trip_id,
            budget_estimate=ai_data.get("budget_estimate"),
            packing_checklist=json.dumps(ai_data.get("packing_checklist")) if isinstance(ai_data.get("packing_checklist"), list) else ai_data.get("packing_checklist"),
            restaurant_recommendations=json.dumps(ai_data.get("restaurant_recommendations")) if isinstance(ai_data.get("restaurant_recommendations"), list) else ai_data.get("restaurant_recommendations"),
            local_attractions=json.dumps(ai_data.get("local_attractions")) if isinstance(ai_data.get("local_attractions"), list) else ai_data.get("local_attractions"),
            weather_suggestions=ai_data.get("weather_suggestions"),
        )
        self.repository.db.add(itinerary)
        
        for dp_data in ai_data.get("day_plans", []):
            day_no = dp_data.get("day_no", 1)
            dp = DayPlan(
                id=uuid.uuid4(),
                itinerary_id=itinerary.id,
                day_no=day_no,
                theme=dp_data.get("theme", "Day Plan"),
                description=dp_data.get("description", "")
            )
            self.repository.db.add(dp)
            
            for act_data in dp_data.get("activities", []):
                scheduled_time_str = act_data.get("scheduled_time")
                from datetime import datetime
                time_obj = None
                if scheduled_time_str:
                    try:
                        time_obj = datetime.strptime(scheduled_time_str, "%H:%M:%S").time()
                    except ValueError:
                        time_obj = None
                        
                act = ItineraryItem(
                    id=uuid.uuid4(),
                    trip_id=trip_id,
                    day_no=day_no,
                    activity=act_data.get("activity", "Activity"),
                    scheduled_time=time_obj,
                    notes=act_data.get("notes"),
                    location=act_data.get("location")
                )
                self.repository.db.add(act)
                
        await self.repository.db.commit()
        return await self.get_ai_itinerary(trip_id, current_user)
        
    async def regenerate_day_plan(self, trip_id: UUID, day_no: int, payload: AIGenerateRequest, current_user: User) -> ItineraryResponse:
        await self._verify_trip_ownership(trip_id, current_user.id)
        trip = await self.trip_repository.get_user_trip(trip_id=trip_id, user_id=current_user.id)
        
        itinerary = await self.repository.db.scalar(select(Itinerary).where(Itinerary.trip_id == trip_id, Itinerary.is_deleted.is_(False)))
        if not itinerary:
            raise ResourceNotFoundException("No AI itinerary found for this trip. Generate a full itinerary first.")
            
        day_plan = await self.repository.db.scalar(select(DayPlan).where(DayPlan.itinerary_id == itinerary.id, DayPlan.day_no == day_no, DayPlan.is_deleted.is_(False)))
        current_theme = day_plan.theme if day_plan else "Free day"
        
        generator = ItineraryGenerator()
        ai_data = await generator.regenerate_day(trip.title, day_no, current_theme, payload.preferences)
        
        # Delete existing ItineraryItems for this day
        await self.repository.db.execute(delete(ItineraryItem).where(ItineraryItem.trip_id == trip_id, ItineraryItem.day_no == day_no))
        
        if day_plan:
            day_plan.theme = ai_data.get("theme", "Day Plan")
            day_plan.description = ai_data.get("description", "")
        else:
            day_plan = DayPlan(
                id=uuid.uuid4(),
                itinerary_id=itinerary.id,
                day_no=day_no,
                theme=ai_data.get("theme", "Day Plan"),
                description=ai_data.get("description", "")
            )
            self.repository.db.add(day_plan)
            
        for act_data in ai_data.get("activities", []):
            scheduled_time_str = act_data.get("scheduled_time")
            from datetime import datetime
            time_obj = None
            if scheduled_time_str:
                try:
                    time_obj = datetime.strptime(scheduled_time_str, "%H:%M:%S").time()
                except ValueError:
                    time_obj = None
                    
            act = ItineraryItem(
                id=uuid.uuid4(),
                trip_id=trip_id,
                day_no=day_no,
                activity=act_data.get("activity", "Activity"),
                scheduled_time=time_obj,
                notes=act_data.get("notes"),
                location=act_data.get("location")
            )
            self.repository.db.add(act)
            
        await self.repository.db.commit()
        return await self.get_ai_itinerary(trip_id, current_user)

    async def add_item(
        self, trip_id: UUID, payload: ItineraryItemCreateRequest, current_user: User
    ) -> ItineraryItemResponse:
        """Add an itinerary item to a trip."""
        logger.info("ItineraryService.add_item: trip_id=%s day=%s", trip_id, payload.day_no)
        await self._verify_trip_ownership(trip_id, current_user.id)

        item = ItineraryItem(
            id=uuid.uuid4(),
            trip_id=trip_id,
            day_no=payload.day_no,
            activity=payload.activity.strip(),
            scheduled_time=payload.scheduled_time,
            notes=payload.notes.strip() if payload.notes else None,
            location=payload.location.strip() if payload.location else None,
        )

        created = await self.repository.create(item)
        return ItineraryItemResponse.model_validate(created)

    async def update_item(
        self, trip_id: UUID, item_id: UUID, payload: ItineraryItemUpdateRequest, current_user: User
    ) -> ItineraryItemResponse:
        """Update or reorder an itinerary item."""
        logger.info("ItineraryService.update_item: item_id=%s", item_id)
        await self._verify_trip_ownership(trip_id, current_user.id)

        item = await self.repository.get_by_id_and_trip(item_id=item_id, trip_id=trip_id)
        if not item:
            raise ResourceNotFoundException("Itinerary item not found in this trip.")

        if payload.day_no is not None:
            item.day_no = payload.day_no
        if payload.activity is not None:
            item.activity = payload.activity.strip()
        if payload.scheduled_time is not None:
            item.scheduled_time = payload.scheduled_time
        if payload.notes is not None:
            item.notes = payload.notes.strip()
        if payload.location is not None:
            item.location = payload.location.strip()

        updated = await self.repository.update(item)
        return ItineraryItemResponse.model_validate(updated)

    async def delete_item(self, trip_id: UUID, item_id: UUID, current_user: User) -> None:
        """Soft-delete an itinerary item."""
        logger.info("ItineraryService.delete_item: item_id=%s", item_id)
        await self._verify_trip_ownership(trip_id, current_user.id)

        item = await self.repository.get_by_id_and_trip(item_id=item_id, trip_id=trip_id)
        if not item:
            raise ResourceNotFoundException("Itinerary item not found in this trip.")

        item.soft_delete()
        await self.repository.update(item)
