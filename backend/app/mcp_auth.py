"""Bearer-token auth middleware for the MCP sub-app."""

from __future__ import annotations

import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Constant-time bearer-token check in front of a mounted ASGI sub-app.

    ``protect_prefix`` is matched against the incoming request path. When this
    middleware is installed on a sub-app that was mounted by FastAPI (with the
    mount prefix already stripped), the relevant prefix is usually ``"/"``.
    """

    def __init__(self, app, token: str, protect_prefix: str = "/") -> None:
        super().__init__(app)
        self._token = token
        self._prefix = protect_prefix

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith(self._prefix):
            return await call_next(request)

        # Let CORS preflight through; the outer app's CORSMiddleware answers it.
        if request.method == "OPTIONS":
            return await call_next(request)

        header = request.headers.get("authorization", "")
        scheme, _, presented = header.partition(" ")
        if scheme.lower() != "bearer" or not presented:
            return JSONResponse(
                {"error": "unauthorized", "detail": "Missing bearer token."},
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="paper-search-mcp"'},
            )
        if not secrets.compare_digest(presented, self._token):
            return JSONResponse(
                {"error": "unauthorized", "detail": "Invalid bearer token."},
                status_code=401,
            )
        return await call_next(request)
