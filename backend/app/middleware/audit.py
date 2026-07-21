import time
import logging
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("audit")


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all authenticated API requests for audit purposes.
    Records: method, path, status code, response time, and user ID (from JWT claims).
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Only log API requests (skip static assets, health checks)
        path = request.url.path
        if path.startswith("/api/") and not path.endswith("/health"):
            # Extract user info from auth header if present
            auth_header = request.headers.get("authorization", "")
            user_info = "anonymous"
            if auth_header.startswith("Bearer "):
                try:
                    import base64
                    import json
                    token = auth_header.split(" ")[1]
                    payload_part = token.split(".")[1]
                    # Add padding
                    payload_part += "=" * (4 - len(payload_part) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_part))
                    user_info = f"user:{payload.get('sub', 'unknown')}"
                except Exception:
                    user_info = "invalid_token"

            logger.info(
                f"[AUDIT] {request.method} {path} -> {response.status_code} "
                f"({duration_ms:.1f}ms) [{user_info}] "
                f"IP:{request.client.host if request.client else 'unknown'}"
            )

        return response


def setup_audit_logging(app: FastAPI) -> None:
    """Register the audit logging middleware."""
    app.add_middleware(AuditLoggingMiddleware)
