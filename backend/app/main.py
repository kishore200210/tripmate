"""
app/main.py

TripMate FastAPI Application Entry Point.

Architecture:
    - Application factory pattern: create_application() builds the app.
    - All routers are registered here after modules are built.
    - Middleware registered in order: CORS -> Global Exception Handlers.
    - Lifespan context manager handles startup/shutdown lifecycle events.
    - print() is NEVER used — structured logging via Python logging module.

Technologies: FastAPI, SQLAlchemy, Sentry, Logfire.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import os
import sentry_sdk
import logfire
from prometheus_fastapi_instrumentator import Instrumentator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError


from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BusinessRuleViolationException,
    ExternalServiceException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    ValidationException,
    InvalidTokenException,
)
from app.core.router import router as system_router

settings = get_settings()

# ── Logger ────────────────────────────────────────────────
# Use Python's logging module — captured by Logfire/Sentry in production.
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

# ── Observability & Monitoring ────────────────────────────

# Initialize Sentry (Bypass gracefully if DSN is missing)
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# Initialize Logfire
if settings.LOGFIRE_TOKEN:
    logfire.configure()
    logfire.instrument_pydantic(record="all")
else:
    logger.info("Logfire skipped: LOGFIRE_TOKEN not set")


# ── Lifespan ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles application startup and shutdown events.
    Startup: log configuration summary, validate connections.
    Shutdown: cleanly release resources.
    """
    logger.info("🚀 %s v%s starting up...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("   Environment : %s", settings.APP_ENV)
    logger.info("   Debug Mode  : %s", settings.DEBUG)
    yield
    logger.info("🛑 %s shutting down cleanly.", settings.APP_NAME)


# ── Application Factory ───────────────────────────────────

def create_application() -> FastAPI:
    """
    Factory function that creates and configures the FastAPI application.
    A factory pattern allows creating a fresh, isolated app instance per test suite.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise AI-Powered Travel Planning Platform",
        docs_url="/docs" if settings.DEBUG else None,    # Hidden in production
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Observability Instrumentation ──────────────────────
    if settings.LOGFIRE_TOKEN:
        logfire.instrument_fastapi(application)
    Instrumentator().instrument(application).expose(application)

    # ── CORS Middleware ────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global Exception Handlers ─────────────────────────
    # Maps domain exceptions -> correct HTTP status codes.
    # Controllers do NOT handle exceptions — they raise domain exceptions only.

    @application.exception_handler(ResourceNotFoundException)
    async def not_found_handler(request: Request, exc: ResourceNotFoundException) -> JSONResponse:
        logger.warning("404 Not Found: %s | path=%s", exc.message, request.url.path)
        return JSONResponse(status_code=404, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(ResourceAlreadyExistsException)
    async def conflict_handler(request: Request, exc: ResourceAlreadyExistsException) -> JSONResponse:
        logger.warning("409 Conflict: %s | path=%s", exc.message, request.url.path)
        return JSONResponse(status_code=409, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(AuthenticationException)
    async def auth_handler(request: Request, exc: AuthenticationException) -> JSONResponse:
        logger.warning("401 Unauthorized: %s | path=%s", exc.message, request.url.path)
        return JSONResponse(status_code=401, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(InvalidTokenException)
    async def invalid_token_handler(request: Request, exc: InvalidTokenException) -> JSONResponse:
        logger.warning("401 Invalid Token: %s | path=%s", exc.message, request.url.path)
        return JSONResponse(status_code=401, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(AuthorizationException)
    async def forbidden_handler(request: Request, exc: AuthorizationException) -> JSONResponse:
        logger.warning("403 Forbidden: %s | path=%s", exc.message, request.url.path)
        return JSONResponse(status_code=403, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(ValidationException)
    async def validation_handler(request: Request, exc: ValidationException) -> JSONResponse:
        logger.warning("422 Validation: %s | path=%s", exc.message, request.url.path)
        return JSONResponse(status_code=422, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(BusinessRuleViolationException)
    async def business_rule_handler(request: Request, exc: BusinessRuleViolationException) -> JSONResponse:
        logger.warning("400 Business Rule: %s | path=%s", exc.message, request.url.path)
        return JSONResponse(status_code=400, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(ExternalServiceException)
    async def external_service_handler(request: Request, exc: ExternalServiceException) -> JSONResponse:
        logger.error("503 External Service: %s | path=%s", exc.message, request.url.path)
        return JSONResponse(status_code=503, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(RequestValidationError)
    async def fast_api_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("422 Unprocessable Entity | path=%s", request.url.path)
        return JSONResponse(status_code=422, content={"error": {"message": "Validation Error", "detail": exc.errors()}})

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("500 Internal Server Error | path=%s", request.url.path)
        msg = "An unexpected error occurred." if not settings.DEBUG else str(exc)
        return JSONResponse(status_code=500, content={"error": {"message": msg, "detail": None}})


    # ── Router Registration ────────────────────────────────
    # System routes (health check) — MVC: extracted to core/router.py
    application.include_router(system_router)

    # Domain routers registered here as each Milestone is completed:
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

    # Serve uploaded static files
    os.makedirs("uploads", exist_ok=True)
    application.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    return application


# ── WSGI App Instance ─────────────────────────────────────
app = create_application()
