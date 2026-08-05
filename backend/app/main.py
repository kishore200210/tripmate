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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BusinessRuleViolationException,
    ExternalServiceException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    ValidationException,
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

    # ── Router Registration ────────────────────────────────
    # System routes (health check) — MVC: extracted to core/router.py
    application.include_router(system_router)

    # Domain routers registered here as each Milestone is completed:
    # from app.modules.users.router import router as users_router
    # application.include_router(users_router, prefix="/api/v1")

    return application


# ── WSGI App Instance ─────────────────────────────────────
app = create_application()
