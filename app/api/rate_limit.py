"""Rate limiting middleware."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware (100 requests per hour per API key)."""

    def __init__(self, app, requests_per_hour: int = None):
        """Initialize rate limiter.

        Args:
            app: FastAPI app
            requests_per_hour: Number of requests allowed per hour
        """
        super().__init__(app)
        self.requests_per_hour = requests_per_hour or settings.api_rate_limit_per_hour
        self.requests: dict[str, list[datetime]] = defaultdict(list)

    def _get_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request header.

        Args:
            request: FastAPI request

        Returns:
            API key or None
        """
        return request.headers.get("X-API-Key")

    def _cleanup_old_requests(self, api_key: str) -> None:
        """Remove requests older than 1 hour.

        Args:
            api_key: API key
        """
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key] if req_time > one_hour_ago
        ]

    def _check_rate_limit(self, api_key: str) -> bool:
        """Check if API key has exceeded rate limit.

        Args:
            api_key: API key

        Returns:
            True if within limit, False if exceeded
        """
        if not api_key:
            return True  # No rate limit for requests without API key (will fail auth)

        self._cleanup_old_requests(api_key)

        if len(self.requests[api_key]) >= self.requests_per_hour:
            return False

        self.requests[api_key].append(datetime.now(UTC))
        return True

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip rate limiting for health check and docs
        if request.url.path in ["/docs", "/openapi.json", "/redoc", "/health"]:
            return await call_next(request)

        api_key = self._get_api_key(request)

        if not self._check_rate_limit(api_key):
            logger.warning(f"Rate limit exceeded for API key: {api_key[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_hour} requests per hour.",
                headers={"Retry-After": "3600"},
            )

        response = await call_next(request)
        return response
