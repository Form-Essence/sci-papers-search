"""Unified Python server for paper-search.

One uvicorn process on one port serves three surfaces:

- ``/``       → the built Next.js UI (static export in ``frontend/out``)
- ``/api/*``  → FastAPI REST endpoints consumed by the UI
- ``/mcp``    → paper-search-mcp streamable-http endpoint (open, no auth)

Host/port and CORS origins live in ``mcp-config.json`` at the repo root.
Optional ``ui_password`` enables a server-side-only gate: the UI loads, but
``/api/*`` (except login/me/health/docs) requires an HMAC-signed session cookie
after ``POST /api/login``.

Run with: ``python -m uvicorn app.main:app --host <host> --port <port>``.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from mcp.server.transport_security import TransportSecuritySettings

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import REPO_ROOT, load_config

APP_CONFIG = load_config()

from paper_search_mcp import server as mcp_server  # noqa: E402
from paper_search_mcp.server import mcp as paper_mcp  # noqa: E402

from .aggregator import search_papers_with_timeout  # noqa: E402
from .clients import build_client_snippets  # noqa: E402
from .schemas import (  # noqa: E402
    DownloadRequest,
    DownloadResponse,
    McpConfigResponse,
    SearchRequest,
    SearchResponse,
    SourcesResponse,
)
from .sources import build_source_list  # noqa: E402
from .ui_auth import UI_SESSION_COOKIE, register_ui_auth, ui_session_token_valid  # noqa: E402

logger = logging.getLogger("paper_search")
logging.basicConfig(level=logging.INFO)


# The MCP Starlette app registers a single route at ``settings.streamable_http_path``
# (default ``/mcp``). When we mount the sub-app under ``/mcp`` in FastAPI, the
# mount strips the prefix before dispatching — so the internal route must be
# ``/`` to match what arrives. Mutate before ``streamable_http_app()`` is called.
paper_mcp.settings.streamable_http_path = "/"

# FastMCP defaults ``host=127.0.0.1``, which turns on MCP DNS rebinding protection
# with localhost-only ``allowed_hosts``. Requests then fail with 421
# "Invalid Host header" when clients use ``public_url`` (e.g. Open Code over HTTPS).
_parsed_public = urlparse(APP_CONFIG.public_url)
_public_hostname = (_parsed_public.hostname or "").strip()
_ts = paper_mcp.settings.transport_security
if _ts is not None and _ts.enable_dns_rebinding_protection and _public_hostname:
    hosts = list(_ts.allowed_hosts)
    for h in (_public_hostname, f"{_public_hostname}:*"):
        if h not in hosts:
            hosts.append(h)
    origins = list(_ts.allowed_origins)
    if _parsed_public.scheme in ("http", "https"):
        for o in (
            f"{_parsed_public.scheme}://{_public_hostname}",
            f"{_parsed_public.scheme}://{_public_hostname}:*",
        ):
            if o not in origins:
                origins.append(o)
    paper_mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=_ts.enable_dns_rebinding_protection,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )

_mcp_app = paper_mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Chain the MCP sub-app's lifespan so its session manager starts/stops."""
    async with _mcp_app.router.lifespan_context(_mcp_app):
        yield


app = FastAPI(
    title="Paper Search",
    version="0.1.0",
    description="Unified Web UI + REST + MCP server on top of paper-search-mcp.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(APP_CONFIG.server.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/me", response_model=None)
async def ui_me(request: Request):
    if not APP_CONFIG.ui_password:
        return {"authenticated": True, "ui_gate": False}
    session = request.cookies.get(UI_SESSION_COOKIE)
    if ui_session_token_valid(APP_CONFIG, session):
        return {"authenticated": True, "ui_gate": True}
    return JSONResponse({"authenticated": False, "ui_gate": True}, status_code=401)


@app.get("/api/sources", response_model=SourcesResponse)
async def list_sources() -> SourcesResponse:
    return SourcesResponse(sources=build_source_list(list(mcp_server.ALL_SOURCES)))


@app.get("/api/mcp-config", response_model=McpConfigResponse)
async def mcp_config() -> McpConfigResponse:
    public = APP_CONFIG.public_url.rstrip("/")
    mcp_url = f"{public}/mcp"
    return build_client_snippets(public_url=public, mcp_url=mcp_url)


@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    try:
        result = await search_papers_with_timeout(
            query=req.query,
            sources=req.sources,
            max_results_per_source=req.max_results_per_source,
            year=req.year,
            per_source_timeout=APP_CONFIG.server.per_source_timeout,
        )
    except Exception as exc:  # defensive; aggregator catches per-source failures already
        logger.exception("search_papers_with_timeout failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SearchResponse(
        query=result.get("query", req.query),
        sources_requested=[result.get("sources_requested", "all")],
        sources_used=list(result.get("sources_used", [])),
        source_results=dict(result.get("source_results", {})),
        errors=dict(result.get("errors", {})),
        papers=list(result.get("papers", [])),
        total=int(result.get("total", 0)),
        raw_total=int(result.get("raw_total", 0)),
    )


@app.post("/api/download", response_model=DownloadResponse)
async def download(req: DownloadRequest) -> DownloadResponse:
    save_path = str(REPO_ROOT / "downloads")
    try:
        result = await mcp_server.download_with_fallback(
            source=req.source,
            paper_id=req.paper_id,
            doi=req.doi,
            title=req.title,
            save_path=save_path,
            use_scihub=req.use_scihub,
        )
    except Exception as exc:
        logger.exception("download_with_fallback failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if isinstance(result, str) and os.path.exists(result):
        return DownloadResponse(ok=True, message="Downloaded.", path=result)

    return DownloadResponse(ok=False, message=str(result))


# UI login/logout routes must be registered *before* ``mount("/", StaticFiles)``.
# Otherwise the catch-all static mount handles ``POST /api/login`` and login never works.
if APP_CONFIG.ui_password:
    logger.info("UI password gate enabled (HMAC session cookie).")
    register_ui_auth(app, APP_CONFIG)
else:
    logger.info(
        "UI login gate is off — set non-empty ui_password in mcp-config.json "
        "and restart to show the password screen.",
    )


class _McpMountAdapter:
    """Forward a Mount's stripped scope to the MCP sub-app.

    When Starlette's ``Mount("/mcp", ...)`` matches ``/mcp/`` it sets
    ``scope["path"]`` to ``"/"``. When it matches ``/mcp`` (no trailing slash)
    the stripped path is ``""`` — normalise that to ``"/"`` so the inner route
    at ``/`` still matches.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and not scope.get("path"):
            scope = {**scope, "path": "/", "raw_path": b"/"}
        await self.inner(scope, receive, send)


class _McpBareAdapter:
    """Dispatch a bare ``/mcp`` request (matched as a plain Route, not a Mount)
    to the MCP sub-app. A Route does not strip the matched prefix, so we have
    to rewrite the scope to pretend the sub-app was mounted at ``/mcp``.
    """

    def __init__(self, inner, mount_path: str = "/mcp"):
        self.inner = inner
        self.mount_path = mount_path

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            scope = {
                **scope,
                "path": "/",
                "raw_path": b"/",
                "root_path": scope.get("root_path", "") + self.mount_path,
            }
        await self.inner(scope, receive, send)


# Matches /mcp/* (with anything after the slash) and /mcp/ (empty remainder).
app.mount("/mcp", _McpMountAdapter(_mcp_app))

# Matches the bare /mcp. Class-based ASGI endpoint so Starlette treats it as
# an ASGI app (not a function-style HTTP endpoint). Must sit before the
# static-files mount added below.
from starlette.routing import Route  # noqa: E402

app.router.routes.append(
    Route("/mcp", endpoint=_McpBareAdapter(_mcp_app), name="mcp_bare")
)

# Serve the built Next.js static export last. html=True makes ``/`` serve
# ``index.html`` from the directory. If the build hasn't been run, skip the
# mount and log a hint — the API and /mcp still work.
_UI_DIR = REPO_ROOT / "frontend" / "out"
if _UI_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
else:
    logger.warning(
        "UI build not found at %s. Run `pnpm --dir frontend build` to create it.",
        _UI_DIR,
    )
