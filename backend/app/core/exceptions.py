"""
app/core/exceptions.py

Custom domain exception hierarchy for TripMate.

Architecture:
    - All business exceptions inherit from a single TripMateException base.
    - Controllers catch these and map them to HTTP responses.
    - Services raise these; they are ignorant of HTTP status codes.

Engineering Principles:
    - Open/Closed: New exceptions extend the hierarchy without modifying it.
    - Single Responsibility: Exceptions carry only error context, not HTTP logic.
"""


class TripMateException(Exception):
    """Base exception for all TripMate domain errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


# ── Resource Exceptions ───────────────────────────────────


class ResourceNotFoundException(TripMateException):
    """Raised when a requested resource does not exist in the database."""

    pass


class ResourceAlreadyExistsException(TripMateException):
    """Raised when attempting to create a resource that already exists (e.g., duplicate email)."""

    pass


# ── Authentication / Authorization Exceptions ─────────────


class AuthenticationException(TripMateException):
    """Raised when credentials are invalid or the token is missing/expired."""

    pass


class AuthorizationException(TripMateException):
    """Raised when a user attempts to perform an action they do not have permission for."""

    pass


class InvalidTokenException(TripMateException):
    """Raised when a JWT token is malformed, expired, or cannot be verified."""

    pass


# ── Validation Exceptions ─────────────────────────────────


class ValidationException(TripMateException):
    """Raised when business-level validation fails (beyond Pydantic schema validation)."""

    pass


class InvalidFileTypeException(TripMateException):
    """Raised when an uploaded file has an unsupported MIME type."""

    pass


# ── External Service Exceptions ───────────────────────────


class ExternalServiceException(TripMateException):
    """Raised when an external API call fails (weather, currency, OpenAI, Cloudinary)."""

    pass


class LLMException(TripMateException):
    """Raised when an LLM call fails or times out."""

    pass


# ── Business Logic Exceptions ─────────────────────────────


class BusinessRuleViolationException(TripMateException):
    """Raised when a business rule is violated (e.g., editing a completed trip)."""

    pass
