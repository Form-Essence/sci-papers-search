#!/usr/bin/env bash
# Local dev runner for the unified paper-search server.
#
# One Python uvicorn process serves:
#   /         -> static Next.js export from frontend/out
#   /api/*    -> FastAPI REST endpoints
#   /mcp      -> paper-search-mcp streamable-http (bearer-token protected)
#
# Pass SKIP_BUILD=1 to reuse an existing frontend/out bundle (the server will
# log a warning and serve nothing at `/` if it's missing).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SKIP_BUILD="${SKIP_BUILD:-0}"

read -r HOST PORT <<< "$(
  "$REPO_ROOT/.venv/bin/python" - <<'PY'
import json
from pathlib import Path
try:
    data = json.loads(Path("mcp-config.json").read_text(encoding="utf-8"))
except Exception:
    data = {}
srv = data.get("server") or {}
print(f"{srv.get('host', '0.0.0.0')} {srv.get('port', 3636)}")
PY
)"

if [[ "$SKIP_BUILD" != "1" ]]; then
    echo "[dev] building Next.js static export..."
    (cd "$REPO_ROOT/frontend" && pnpm build)
fi

echo "[dev] starting paper-search on http://${HOST}:${PORT}"
cd "$REPO_ROOT/backend"
exec "$REPO_ROOT/.venv/bin/python" -m uvicorn app.main:app \
    --host "$HOST" --port "$PORT" --reload \
    --reload-dir "$REPO_ROOT/backend/app"
