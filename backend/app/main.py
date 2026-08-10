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

from app.modules.recommendations.model_loader import ModelLoader
from app.modules.computer_vision.model_loader import YoloModelLoader

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles application startup and shutdown events.
    Startup: log configuration summary, validate connections, load ML model.
    Shutdown: cleanly release resources.
    """
    logger.info("🚀 %s v%s starting up...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("   Environment : %s", settings.APP_ENV)
    logger.info("   Debug Mode  : %s", settings.DEBUG)
    
    ModelLoader.load()
    YoloModelLoader.load()
    
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
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    # ── Global Exception Handlers ─────────────────────────
    # Maps domain exceptions -> correct HTTP status codes.
    from app.core.exceptions_handler import register_exception_handlers
    register_exception_handlers(application)


    # ── Router Registration ────────────────────────────────
    from app.core.router_registry import register_all_routers
    register_all_routers(application)

    # Serve uploaded static files
    os.makedirs("uploads", exist_ok=True)
    application.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    
    # Serve static files (like PDFs)
    os.makedirs("static/pdfs", exist_ok=True)
    application.mount("/static", StaticFiles(directory="static"), name="static")

    return application


# ── WSGI App Instance ─────────────────────────────────────
app = create_application()
