#!/usr/bin/env bash
# Generate a random bearer token for the unified paper-search server and
# (re)write it into mcp-config.json. Running twice rotates the secret.
# Preserves existing `server.*` values (host, port, cors_origins, api_keys).
#
# Optional:
#   PAPER_SEARCH_MCP_PUBLIC_URL   Override the public URL baked into the
#                                 client snippets (e.g. your Cloudflare
#                                 Tunnel hostname).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CONFIG_FILE="$REPO_ROOT/mcp-config.json"
EXAMPLE_FILE="$REPO_ROOT/mcp-config.example.json"

PY="$REPO_ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

PAPER_SEARCH_MCP_PUBLIC_URL="${PAPER_SEARCH_MCP_PUBLIC_URL:-}" \
  CONFIG_FILE="$CONFIG_FILE" \
  EXAMPLE_FILE="$EXAMPLE_FILE" \
  "$PY" <<'PYEOF'
import json
import os
import secrets
from pathlib import Path

config_path = Path(os.environ["CONFIG_FILE"])
example_path = Path(os.environ["EXAMPLE_FILE"])
override_url = os.environ.get("PAPER_SEARCH_MCP_PUBLIC_URL", "").strip()

if config_path.exists():
    data = json.loads(config_path.read_text(encoding="utf-8"))
elif example_path.exists():
    data = json.loads(example_path.read_text(encoding="utf-8"))
else:
    data = {}

token = secrets.token_urlsafe(32)
public_url = (override_url or data.get("public_url") or "http://localhost:3636").rstrip("/")

data["_comment"] = (
    "Single source of truth. Server reads `server`; clients paste from `clients`. "
    "Regenerate the token with ./scripts/gen-token.sh."
)
data["auth_token"] = token
data["public_url"] = public_url

# Migrate from the old three-server shape if it's still present.
server = data.get("server") or {}
legacy_keys = {"backend", "frontend", "mcp"}
if any(k in server for k in legacy_keys):
    api_keys = server.get("api_keys") or {}
    server = {}
    server["api_keys"] = api_keys
data["server"] = server

server.setdefault("host", "0.0.0.0")
server.setdefault("port", 3636)
server.setdefault("cors_origins", ["*"])
server.setdefault("api_keys", {
    "unpaywall_email": "",
    "core_api_key": "",
    "semantic_scholar_api_key": "",
    "google_scholar_proxy_url": "",
    "zenodo_access_token": "",
    "doaj_api_key": "",
    "ieee_api_key": "",
    "acm_api_key": "",
})

mcp_url = f"{public_url}/mcp"
auth_header = f"Bearer {token}"

data["clients"] = {
    "cursor_mcp_json": {
        "mcpServers": {
            "paper-search": {
                "url": mcp_url,
                "headers": {"Authorization": auth_header},
            }
        }
    },
    "lm_studio_mcp_json": {
        "mcpServers": {
            "paper-search": {
                "url": mcp_url,
                "headers": {"Authorization": auth_header},
            }
        }
    },
    "opencode_config": {
        "mcp": {
            "paper-search": {
                "type": "remote",
                "url": mcp_url,
                "headers": {"Authorization": auth_header},
                "enabled": True,
            }
        }
    },
    "openai_responses_api_snippet": {
        "tools": [
            {
                "type": "mcp",
                "server_label": "paper-search",
                "server_url": mcp_url,
                "headers": {"Authorization": auth_header},
                "require_approval": "never",
            }
        ]
    },
    "curl_smoke_test": (
        f"curl -N -X POST '{mcp_url}' "
        f"-H 'Authorization: {auth_header}' "
        f"-H 'Content-Type: application/json' "
        f"-H 'Accept: application/json, text/event-stream' "
        f"-d '{{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}}'"
    ),
}

config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"wrote {config_path}")
print(f"token: {token}")
print(f"public_url: {public_url}")
PYEOF

chmod 600 "$CONFIG_FILE" 2>/dev/null || true

echo ""
echo "Next: restart the paper-search server so it picks up the new token:"
echo "  ./stop.sh && ./start.sh"
