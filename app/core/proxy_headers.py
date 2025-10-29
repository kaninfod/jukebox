from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Awaitable
from fastapi import Request


class SimpleProxyHeaderMiddleware(BaseHTTPMiddleware):
    """
    Minimal middleware to respect X-Forwarded-Proto from a trusted reverse proxy.

    Purpose: Ensure downstream middlewares (e.g., HTTPSRedirect) see the correct
    request.scheme when running behind Nginx Proxy Manager / Cloudflare, fixing
    WebSocket upgrade issues caused by unwanted HTTP->HTTPS redirects.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        xf_proto = request.headers.get("x-forwarded-proto") or request.headers.get("X-Forwarded-Proto")
        if xf_proto:
            # Use the first value if multiple are provided
            scheme = xf_proto.split(",")[0].strip()
            if scheme:
                request.scope["scheme"] = scheme
        return await call_next(request)

