from fastapi import FastAPI

from app.core.router import router as system_router
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.destinations.router import router as destinations_router
from app.modules.trips.router import router as trips_router
from app.modules.itineraries.router import router as itineraries_router
from app.modules.bookings.router import router as bookings_router
from app.modules.reviews.router import router as reviews_router
from app.modules.ai_concierge.router import router as ai_concierge_router
from app.modules.rag.router import router as rag_router
from app.modules.ai_agent.router import router as ai_agent_router
from app.modules.pdf.router import router as pdf_router
from app.modules.vision.router import router as vision_router
from app.modules.places.router import router as places_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.computer_vision.router import router as computer_vision_router
from app.modules.analytics.router import router as analytics_router

def register_all_routers(application: FastAPI) -> None:
    """Registers all domain and system routers to the FastAPI application."""
    # System routes (health check)
    application.include_router(system_router)

    # Domain routers
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(users_router, prefix="/api/v1")
    application.include_router(destinations_router, prefix="/api/v1")
    application.include_router(trips_router, prefix="/api/v1")
    application.include_router(itineraries_router, prefix="/api/v1")
    application.include_router(bookings_router, prefix="/api/v1")
    application.include_router(reviews_router, prefix="/api/v1")
    application.include_router(ai_concierge_router, prefix="/api/v1")
    application.include_router(rag_router, prefix="/api/v1")
    application.include_router(ai_agent_router, prefix="/api/v1")
    application.include_router(pdf_router, prefix="/api/v1")
    application.include_router(vision_router, prefix="/api/v1")
    application.include_router(places_router, prefix="/api/v1")
    application.include_router(recommendations_router, prefix="/api/v1")
    application.include_router(computer_vision_router, prefix="/api/v1")
    application.include_router(analytics_router, prefix="/api/v1")
