from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Awaitable
import logging

from app.config import config

logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect all /api/* routes using an API key.

    Behavior:
    - If config.API_KEY is set: require header X-API-Key to match, or Authorization: Bearer <token>.
    - If config.API_KEY is NOT set: allow requests only from localhost (127.0.0.1, ::1) when ALLOW_LOCAL_API_BYPASS is true.
    """

    def __init__(self, app):
        super().__init__(app)
        self._localhost_hosts = {"127.0.0.1", "::1"}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        path = request.url.path
        # Only protect API routes
        if not path.startswith("/api/"):
            return await call_next(request)

        client_host = (request.client.host if request.client else None)

        # Allow localhost for internal server-side calls if enabled
        if config.ALLOW_LOCAL_API_BYPASS and client_host in self._localhost_hosts:
            return await call_next(request)

        # If API key configured, enforce header check
        if config.API_KEY:
            # Accept either custom header X-API-Key or Authorization: Bearer <token>
            api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
            if not api_key:
                auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
                if auth_header and isinstance(auth_header, str):
                    parts = auth_header.split(" ", 1)
                    if len(parts) == 2 and parts[0].lower() == "bearer":
                        api_key = parts[1]
            if not api_key or api_key != config.API_KEY:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized: missing or invalid API key"}
                )
            return await call_next(request)

        # No API key set and not localhost: deny
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized: API disabled for public access without API_KEY"}
        )
