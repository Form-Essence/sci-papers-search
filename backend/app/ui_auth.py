"""Optional UI gate: password on the server, stateless HMAC session cookie.

Same model as RAG_horizon ``server.py``: signed cookie survives multiple
workers; ASGI middleware (not ``BaseHTTPMiddleware``) so MCP streamable HTTP
keeps streaming.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from http.cookies import SimpleCookie
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .config import AppConfig
from .schemas import LoginRequest

UI_SESSION_COOKIE = "session"
_SESSION_TTL_SEC = 86400 * 7
_UI_SALT = "paper-search-ui"


def _signing_key(cfg: AppConfig) -> bytes:
    raw = (cfg.session_secret or cfg.auth_token or "").strip()
    if raw:
        return hashlib.sha256(raw.encode("utf-8")).digest()
    return hashlib.sha256(f"{_UI_SALT}|{cfg.ui_password}".encode("utf-8")).digest()


def issue_ui_session_token(cfg: AppConfig) -> str:
    ts = int(time.time())
    nonce = secrets.token_urlsafe(16)
    payload = f"{ts}.{nonce}"
    sig = hmac.new(
        _signing_key(cfg), payload.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{sig}"


def ui_session_token_valid(cfg: AppConfig, token: Optional[str]) -> bool:
    if not token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    ts_s, nonce, sig = parts[0], parts[1], parts[2]
    if not ts_s.isdigit() or not nonce or not sig:
        return False
    ts = int(ts_s)
    if ts + _SESSION_TTL_SEC < int(time.time()):
        return False
    payload = f"{ts_s}.{nonce}"
    expected = hmac.new(
        _signing_key(cfg), payload.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig)


def _scope_header(scope: Scope, name: bytes) -> Optional[str]:
    for k, v in scope.get("headers") or []:
        if k == name:
            return v.decode("latin-1")
    return None


def _scope_cookie(scope: Scope, cookie_name: str) -> Optional[str]:
    cookie = _scope_header(scope, b"cookie")
    if not cookie:
        return None
    jar = SimpleCookie()
    try:
        jar.load(cookie)
    except Exception:
        return None
    morsel = jar.get(cookie_name)
    return morsel.value if morsel else None


async def _asgi_json_response(send: Send, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


class PaperSearchUIAuthMiddleware:
    """Require a valid UI session cookie for ``/api/*`` (except auth + health)."""

    def __init__(self, app: ASGIApp, cfg: AppConfig):
        self.app = app
        self._cfg = cfg
        self._public = (
            "/api/login",
            "/api/logout",
            "/api/me",
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope.get("method") == "OPTIONS":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""

        if path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        if any(path == p or path.startswith(p + "/") for p in self._public):
            await self.app(scope, receive, send)
            return

        session = _scope_cookie(scope, UI_SESSION_COOKIE)
        if not ui_session_token_valid(self._cfg, session):
            if path == "/" or not path.startswith("/api/"):
                await self.app(scope, receive, send)
                return
            await _asgi_json_response(send, 401, {"error": "unauthorized"})
            return

        await self.app(scope, receive, send)


def register_ui_auth(app: FastAPI, cfg: AppConfig) -> None:
    app.add_middleware(PaperSearchUIAuthMiddleware, cfg=cfg)

    @app.post("/api/login")
    async def ui_login(body: LoginRequest) -> JSONResponse:
        if body.password.strip() != cfg.ui_password:
            return JSONResponse({"error": "wrong password"}, status_code=401)
        token = issue_ui_session_token(cfg)
        resp = JSONResponse({"ok": True})
        resp.set_cookie(
            UI_SESSION_COOKIE,
            token,
            httponly=True,
            samesite="lax",
            max_age=_SESSION_TTL_SEC,
            path="/",
        )
        return resp

    @app.post("/api/logout")
    async def ui_logout() -> JSONResponse:
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(UI_SESSION_COOKIE, path="/")
        return resp
