import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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

logger = logging.getLogger(__name__)
settings = get_settings()

def register_exception_handlers(application: FastAPI) -> None:
    """Registers all global exception handlers onto the FastAPI application."""

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
        # Pydantic v2 puts a ValueError object inside exc.errors()[i]['ctx']['error'].
        # json.dumps cannot serialise Exception instances — stringify ctx values.
        safe_errors = []
        for err in exc.errors():
            safe_err = dict(err)
            if "ctx" in safe_err and isinstance(safe_err["ctx"], dict):
                safe_err["ctx"] = {k: str(v) for k, v in safe_err["ctx"].items()}
            safe_errors.append(safe_err)
        return JSONResponse(status_code=422, content={"error": {"message": "Validation Error", "detail": safe_errors}})

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("500 Internal Server Error | path=%s", request.url.path)
        msg = "An unexpected error occurred." if not settings.DEBUG else str(exc)
        return JSONResponse(status_code=500, content={"error": {"message": msg, "detail": None}})
