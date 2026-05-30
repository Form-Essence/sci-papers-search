#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v pm2 &> /dev/null; then
    echo "Error: PM2 is not installed. Please install it with: npm install -g pm2"
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    echo "Error: pnpm is not installed. Please install it with: npm install -g pnpm"
    exit 1
fi

if [ ! -d ".venv" ] || [ ! -x ".venv/bin/python" ]; then
    echo "Error: Python virtual environment not found at .venv"
    echo "Please run the install steps in README.md first:"
    echo "  uv venv --python 3.12 .venv"
    echo "  source .venv/bin/activate"
    echo "  uv pip install -e ./paper-search-mcp -e ./backend"
    exit 1
fi

if [ ! -f "mcp-config.json" ]; then
    echo "mcp-config.json not found — creating from example..."
    ./scripts/gen-token.sh
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    (cd frontend && pnpm install)
fi

echo "Building Next.js static export..."
(cd frontend && pnpm build)

if [ ! -d "frontend/out" ]; then
    echo "Error: frontend/out not found after build."
    exit 1
fi

mkdir -p logs

echo "Starting paper-search with PM2..."
pm2 start ecosystem.config.js

# Pull host/port from mcp-config.json for the summary message.
read -r HOST PORT <<< "$(.venv/bin/python - <<'PY'
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

DISPLAY_HOST="$HOST"
if [ "$HOST" = "0.0.0.0" ]; then
    DISPLAY_HOST="localhost"
fi

echo ""
echo "✓ paper-search started successfully!"
echo ""
echo "  • Web UI + REST  http://${DISPLAY_HOST}:${PORT}/"
echo "  • MCP endpoint   http://${DISPLAY_HOST}:${PORT}/mcp   (open, no auth)"
echo ""
echo "Run './status.sh' to check status"
echo "Run './log.sh' to view logs"
