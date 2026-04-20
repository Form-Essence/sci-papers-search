# paper-search-backend

Unified FastAPI app that reuses the `paper-search-mcp` Python library to power
three surfaces in a single process:

- `/` — the built Next.js static UI from `frontend/out` (if present).
- `/api/*` — REST endpoints for the UI.
- `/mcp` — paper-search-mcp `streamable-http` endpoint, bearer-token protected.

REST endpoints:

- `GET  /api/health` — liveness probe.
- `GET  /api/sources` — list of source keys and labels currently enabled.
- `POST /api/search`  — unified multi-source search. See `app/schemas.py`.
- `POST /api/download` — OA-first download with fallback chain.

Run from the repo root:

```bash
uv run --directory backend uvicorn app.main:app --reload --host 0.0.0.0 --port 3636
```

(Host/port come from `server.host` / `server.port` in `mcp-config.json` when
launched via the `./start.sh` / `scripts/dev.sh` lifecycle scripts.)
