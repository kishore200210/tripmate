"""
app/main.py

TripMate FastAPI Application Entry Point.

Architecture:
    - Application factory pattern: create_application() builds the app.
    - All routers will be registered here as modules are built.
    - Middleware registered in order: CORS -> Logging -> Error handling.
    - Lifespan context manager handles startup/shutdown events.

Technologies: FastAPI, SQLAlchemy, Sentry, Logfire.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    ResourceAlreadyExistsException,
    ValidationException,
    ExternalServiceException,
    BusinessRuleViolationException,
)

settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles application startup and shutdown events.
    - Startup: Validate connections, warm up models, etc.
    - Shutdown: Cleanly close resources.
    """
    # Startup
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    print(f"   Environment : {settings.APP_ENV}")
    print(f"   Debug Mode  : {settings.DEBUG}")
    yield
    # Shutdown
    print(f"🛑 {settings.APP_NAME} shutting down...")


# ── Application Factory ───────────────────────────────────

def create_application() -> FastAPI:
    """
    Factory function that creates and configures the FastAPI application.
    Using a factory pattern allows easy testing (create a fresh app per test).
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise AI-Powered Travel Planning Platform",
        docs_url="/docs" if settings.DEBUG else None,   # Hide docs in production
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
    # Map domain exceptions to HTTP responses — Controllers stay clean.

    @application.exception_handler(ResourceNotFoundException)
    async def not_found_handler(request: Request, exc: ResourceNotFoundException) -> JSONResponse:
        return JSONResponse(status_code=404, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(ResourceAlreadyExistsException)
    async def conflict_handler(request: Request, exc: ResourceAlreadyExistsException) -> JSONResponse:
        return JSONResponse(status_code=409, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(AuthenticationException)
    async def auth_handler(request: Request, exc: AuthenticationException) -> JSONResponse:
        return JSONResponse(status_code=401, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(AuthorizationException)
    async def forbidden_handler(request: Request, exc: AuthorizationException) -> JSONResponse:
        return JSONResponse(status_code=403, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(ValidationException)
    async def validation_handler(request: Request, exc: ValidationException) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(BusinessRuleViolationException)
    async def business_rule_handler(request: Request, exc: BusinessRuleViolationException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": {"message": exc.message, "detail": exc.detail}})

    @application.exception_handler(ExternalServiceException)
    async def external_service_handler(request: Request, exc: ExternalServiceException) -> JSONResponse:
        return JSONResponse(status_code=503, content={"error": {"message": exc.message, "detail": exc.detail}})

    # ── Health Check ──────────────────────────────────────
    @application.get("/health", tags=["System"])
    async def health_check() -> dict:
        """
        Public health check endpoint.
        Used by Docker, Render, and load balancers to verify the service is alive.
        """
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }

    # ── Router Registration ────────────────────────────────
    # Routers will be registered here as modules are built.
    # Example (Milestone 2+):
    # from app.modules.users.router import router as users_router
    # application.include_router(users_router, prefix="/api/v1")

    return application


# ── WSGI App Instance ─────────────────────────────────────
app = create_application()
