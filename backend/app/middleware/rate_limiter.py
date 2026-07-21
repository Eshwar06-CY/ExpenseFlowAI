import time
import logging
from collections import defaultdict
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# In-memory rate limiting store
# Structure: { ip_address: { path: [timestamp1, timestamp2, ...] } }
_rate_store = defaultdict(lambda: defaultdict(list))

# Configuration: path_prefix -> (max_requests, window_seconds)
RATE_LIMITS = {
    "/api/v1/auth/login": (5, 60),       # 5 attempts per minute
    "/api/v1/auth/register": (3, 60),     # 3 attempts per minute
    "/api/v1/auth/refresh": (10, 60),     # 10 attempts per minute
}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiter for authentication endpoints.
    Tracks request counts per IP + path within a sliding window.
    """

    async def dispatch(self, request: Request, call_next):
        from app.core.config import settings
        
        # Bypass rate limiting in testing and development to avoid 429 errors during automated test runs
        if settings.ENVIRONMENT in {"testing", "development"}:
            return await call_next(request)

        # Only rate-limit specific paths
        path = request.url.path
        limit_config = None
        for prefix, config in RATE_LIMITS.items():
            if path.startswith(prefix):
                limit_config = config
                break

        if limit_config and request.method == "POST":
            max_requests, window = limit_config
            
            # Resolve client IP (checks proxy headers)
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.headers.get("x-real-ip", request.client.host if request.client else "unknown")
                
            now = time.time()

            # Clean old entries outside the window
            _rate_store[client_ip][path] = [
                ts for ts in _rate_store[client_ip][path] if now - ts < window
            ]

            if len(_rate_store[client_ip][path]) >= max_requests:
                logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "detail": "Too many requests. Please try again later.",
                        "error_code": "RATE_LIMITED",
                    },
                )

            _rate_store[client_ip][path].append(now)

        response = await call_next(request)
        return response


def setup_rate_limiter(app: FastAPI) -> None:
    """Register the rate limiter middleware."""
    app.add_middleware(RateLimiterMiddleware)
