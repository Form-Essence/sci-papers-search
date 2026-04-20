#!/usr/bin/env bash
# Starts the paper-search-mcp server over stdio using the shared .venv at the repo root.
# LLM clients (Claude Desktop, LM Studio, Cursor, OpenAI-MCP bridges) should spawn this script.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

exec uv run --directory "$REPO_ROOT/paper-search-mcp" -m paper_search_mcp.server "$@"
