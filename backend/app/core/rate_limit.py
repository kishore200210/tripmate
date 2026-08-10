"""
app/core/rate_limit.py

Reusable Redis-backed rate limiter utility for FastAPI routes.
"""

import time
import logging
from fastapi import Request, HTTPException, status
import redis.asyncio as redis
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RedisRateLimiter:
    """Redis-backed rate limiter using a sliding/fixed window counter."""
    _redis = None

    @classmethod
    def get_redis_client(cls):
        """Lazy initialization of a shared Redis client."""
        if cls._redis is None:
            try:
                cls._redis = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0
                )
            except Exception as e:
                logger.error("Failed to initialize Redis connection for rate limiting: %s", str(e))
        return cls._redis

    def __init__(self, limit: int, window: int = 60) -> None:
        self.limit = limit
        self.window = window

    async def is_rate_limited(self, identifier: str) -> tuple[bool, int]:
        """
        Check if request limit is exceeded for identifier in the current time window.
        Returns a tuple: (is_limited, retry_after_seconds)
        """
        client = self.get_redis_client()
        if client is None:
            # Safe fallback: Allow requests if Redis is unavailable
            return False, 0

        try:
            now = int(time.time())
            window_bucket = now // self.window
            redis_key = f"rate_limit:{identifier}:{window_bucket}"

            # Execute increment and expiration atomically using pipeline
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, self.window + 2)
            results = await pipe.execute()

            request_count = results[0]
            if request_count > self.limit:
                retry_after = self.window - (now % self.window)
                return True, retry_after

            return False, 0
        except Exception as e:
            logger.error("Redis rate limit check failed: %s. Access allowed.", str(e))
            # Safe fallback: Allow requests on network or Redis failures
            return False, 0


class RateLimiter:
    """FastAPI route dependency wrapper for RedisRateLimiter."""

    def __init__(self, limit: int, window: int = 60) -> None:
        self.limiter = RedisRateLimiter(limit=limit, window=window)

    async def __call__(self, request: Request) -> None:
        # Default identifier: client IP address
        identifier = request.client.host if request.client else "unknown"

        # Check Authorization header to support per-user rate limiting if authenticated
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                from jose import jwt
                from app.core.config import settings as app_settings
                payload = jwt.decode(token, app_settings.SECRET_KEY, algorithms=[app_settings.ALGORITHM])
                if "sub" in payload:
                    identifier = payload["sub"]
            except Exception:
                # Token decode failed or key invalid; fall back to client IP
                pass

        is_limited, retry_after = await self.limiter.is_rate_limited(identifier)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests. Please try again later.",
                headers={"Retry-After": str(retry_after)}
            )
