# paper-search

A self-hosted academic paper search service built on top of [`openags/paper-search-mcp`](https://github.com/openags/paper-search-mcp). One `uvicorn` process on one port exposes three surfaces:

| Path | What it is | Who uses it |
|---|---|---|
| `/` | Next.js 15 + shadcn/ui static web app | Humans, in a browser |
| `/api/*` | FastAPI REST endpoints | The web UI |
| `/mcp` | Streamable-HTTP MCP server (bearer-token protected) | LLM clients — Cursor, LM Studio, opencode, OpenAI Responses API, Claude Code, … |

A separate **stdio** MCP entry point is kept for clients that don't speak HTTP MCP yet (e.g. Claude Desktop).

The idea: run it on a Raspberry Pi (or any box), expose it over a Cloudflare Tunnel, and any LLM with MCP support can now search arXiv / PubMed / Unpaywall / CORE / Semantic Scholar / Google Scholar / Zenodo / DOAJ / IEEE / ACM through a single authenticated URL.

## Repository layout

```text
paper-search/
  paper-search-mcp/         upstream clone, installed editable into .venv
  backend/
    app/config.py           loads mcp-config.json, populates os.environ for upstream
    app/main.py             unified FastAPI app: / + /api/* + /mcp
    app/mcp_auth.py         bearer-token middleware for /mcp
  frontend/                 Next.js 15 + shadcn/ui (built as static export to frontend/out)
  scripts/
    dev.sh                  build UI once, run `uvicorn --reload`
    gen-token.sh            rotate bearer token + refresh client snippets
    run-mcp.sh              start local stdio MCP server (Claude Desktop)
  mcp-config.json           single source of truth (gitignored)
  mcp-config.example.json   committable template
  ecosystem.config.js       PM2 config
  start.sh / stop.sh / status.sh / log.sh   PM2 lifecycle
```

Everything — token, host, port, CORS, API keys, ready-to-paste client snippets — lives in **`mcp-config.json`**. No `.env` files.

## Prerequisites

- macOS or Linux (tested on Raspberry Pi OS)
- [`uv`](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+ and `pnpm`
- `pm2` (only if you want the PM2 lifecycle scripts: `npm i -g pm2`)
- `cloudflared` (optional — only if you want to expose it over the internet)

## Install

```bash
git clone <this-repo> paper-search
cd paper-search

git clone https://github.com/openags/paper-search-mcp.git

uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e ./paper-search-mcp -e ./backend

cd frontend && pnpm install && cd ..

cp mcp-config.example.json mcp-config.json
./scripts/gen-token.sh
```

Then open `mcp-config.json` and fill in anything you need under `server.api_keys` (at minimum `unpaywall_email` to enable Unpaywall). Host, port, CORS origins and the bearer token live in the same file.

## Run

### Development (auto-reload)

```bash
./scripts/dev.sh
```

1. Runs `pnpm build` once to produce `frontend/out/` (set `SKIP_BUILD=1` to skip).
2. Starts `uvicorn app.main:app --reload` on `server.host:server.port` from `mcp-config.json` (default `0.0.0.0:3636`).

Open http://localhost:3636.

> UI changes require rerunning `pnpm build` (or `./scripts/dev.sh`). That's the tradeoff for having a single process on a single port.

### Production / Raspberry Pi (PM2)

```bash
./start.sh     # build frontend, then `pm2 start ecosystem.config.js`
./status.sh    # pm2 status + pm2 describe paper-search
./log.sh       # stream logs (see --help for --error / --out / --lines)
./stop.sh      # pm2 stop paper-search
```

To survive reboots: `pm2 save && pm2 startup` once, then `./start.sh` on every deploy.

### Expose over the internet (Cloudflare Tunnel, optional)

```bash
cloudflared tunnel login
cloudflared tunnel create paper-search
cloudflared tunnel route dns paper-search papers.example.com
```

`~/.cloudflared/config.yml`:

```yaml
tunnel: paper-search
credentials-file: /home/pi/.cloudflared/<uuid>.json

ingress:
  - hostname: papers.example.com
    service: http://127.0.0.1:3636
  - service: http_status:404
```

Run it (`cloudflared tunnel run paper-search`, or install as a service) and regenerate the client snippets with the public URL baked in:

```bash
PAPER_SEARCH_MCP_PUBLIC_URL=https://papers.example.com ./scripts/gen-token.sh
```

> **Security.** `/mcp` is bearer-token gated; `/` and `/api/*` are **not**. If you expose the whole host publicly, either restrict the tunnel ingress to `/mcp*`, put Cloudflare Access in front of the hostname, or keep the UI on a LAN-only path.

## Generating / rotating the bearer token

The bearer token that protects `/mcp` lives in `mcp-config.json` under `auth_token`. **Never edit it by hand** — always use the helper script so the matching client snippets under `clients.*` stay in sync.

```bash
./scripts/gen-token.sh
```

What it does:

1. Generates a fresh URL-safe random secret (`secrets.token_urlsafe(32)` — 256 bits of entropy, ~43 chars).
2. Writes it to `auth_token` in `mcp-config.json`, preserving `server.*` (host, port, CORS, API keys).
3. Regenerates every `clients.*` snippet (Cursor, LM Studio, opencode, OpenAI, curl) with the new token baked in.
4. `chmod 600 mcp-config.json` so only your user can read it.

Bake a public URL into the snippets (useful when you expose the service over a Cloudflare Tunnel):

```bash
PAPER_SEARCH_MCP_PUBLIC_URL=https://papers.example.com ./scripts/gen-token.sh
```

After rotating, **restart the server** so it picks up the new token, then re-paste the snippet into each client:

```bash
./stop.sh && ./start.sh          # PM2
# or just Ctrl-C and rerun ./scripts/dev.sh
```

Prefer a specific token (e.g. one issued by a password manager)? Generate it yourself and plug it in — the server only cares that `auth_token` matches the `Authorization: Bearer …` header. You can use any of:

```bash
openssl rand -base64 32 | tr -d '=+/' | cut -c1-43
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
head -c 32 /dev/urandom | base64 | tr -d '=+/' | cut -c1-43
```

Then edit `mcp-config.json` manually (set `auth_token` and update each `Authorization` header under `clients.*`) and restart the server. Running `gen-token.sh` again will overwrite this custom token with a fresh random one.

> If the token ever leaks — committed to git, pasted in a screenshot, sent in chat — rotate immediately with `./scripts/gen-token.sh`, restart, and re-paste into every client.

## Hook up a client

After `gen-token.sh` runs, ready-to-paste snippets sit under `clients.*` in `mcp-config.json`. Shapes below — replace `https://papers.example.com` and `<TOKEN>` with yours.

**Cursor** — `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "paper-search": {
      "url": "https://papers.example.com/mcp",
      "headers": { "Authorization": "Bearer <TOKEN>" }
    }
  }
}
```

**LM Studio** (≥ 0.3.17) — in the chat window, open the right-hand **Program** sidebar → **Install** → **Edit mcp.json**, then paste:

```json
{
  "mcpServers": {
    "paper-search": {
      "url": "https://papers.example.com/mcp",
      "headers": { "Authorization": "Bearer <TOKEN>" }
    }
  }
}
```

Save, toggle the `paper-search` server on, then start a chat with a tool-use-capable model — the `paper-search` tools will appear in the tools list. If the server runs on a different machine than LM Studio, replace `localhost` / `papers.example.com` with the reachable hostname or LAN IP (and make sure `server.cors_origins` / the tunnel ingress allows it).

**opencode** — `~/.config/opencode/opencode.json`:

```json
{
  "mcp": {
    "paper-search": {
      "type": "remote",
      "url": "https://papers.example.com/mcp",
      "headers": { "Authorization": "Bearer <TOKEN>" },
      "enabled": true
    }
  }
}
```

**OpenAI Responses API**:

```python
from openai import OpenAI
client = OpenAI()
resp = client.responses.create(
    model="gpt-5",
    tools=[{
        "type": "mcp",
        "server_label": "paper-search",
        "server_url": "https://papers.example.com/mcp",
        "headers": {"Authorization": "Bearer <TOKEN>"},
        "require_approval": "never",
    }],
    input="Find me five recent papers on state-space models and summarise them.",
)
```

**Claude Desktop** (stdio only — Claude Desktop doesn't support remote MCP yet):

```json
{
  "mcpServers": {
    "paper-search": {
      "command": "/abs/path/to/paper-search/scripts/run-mcp.sh"
    }
  }
}
```

**Smoke test from any machine**:

```bash
curl -N -X POST https://papers.example.com/mcp \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```

Missing/wrong token → `401 Unauthorized`. Valid token → `initialize` handshake over SSE.

## Configuration reference

Everything is in `mcp-config.json`. Template: [`mcp-config.example.json`](./mcp-config.example.json).

```jsonc
{
  "auth_token": "…",                 // bearer token for /mcp (rotated by gen-token.sh)
  "public_url": "http://localhost:3636",
  "server": {
    "host": "0.0.0.0",
    "port": 3636,
    "cors_origins": ["*"],           // tighten to ["https://papers.example.com"] if you like
    "api_keys": {
      "unpaywall_email": "",         // required to enable Unpaywall
      "core_api_key": "",
      "semantic_scholar_api_key": "",
      "google_scholar_proxy_url": "",
      "zenodo_access_token": "",
      "doaj_api_key": "",
      "ieee_api_key": "",
      "acm_api_key": ""
    }
  },
  "clients": { /* pastable snippets for Cursor, LM Studio, opencode, OpenAI, curl */ }
}
```

- The backend (`backend/app/config.py`) loads this file at startup and pushes any non-empty `api_keys.*` value into `os.environ` as the matching `PAPER_SEARCH_MCP_*` var, so the upstream [`get_env`](./paper-search-mcp/paper_search_mcp/config.py) helper picks them up transparently.
- The frontend uses `output: "export"` and calls the API via same-origin relative paths (`fetch("/api/search")`), so there is no base URL to configure.
- PM2 reads `server.host` / `server.port` to launch `uvicorn`.
- Override the config path with `PAPER_SEARCH_CONFIG=/path/to/other.json` before starting the server.

## Architecture

```text
┌──────────────── Browser ───────────────┐
│ http://pi:3636/       ─► static UI     │
│ fetch("/api/search")  ─► FastAPI       │
└─────────────────────────────────────────┘
                   │ same origin
                   ▼
     ┌─────────────────────────────────┐         ┌──── stdio ────► scripts/run-mcp.sh (Claude Desktop)
     │   uvicorn app.main:app  :3636   │         │
     │ ┌────────┬──────────┬────────┐  │ ◄───────┤
     │ │   /    │  /api/*  │  /mcp  │  │   HTTPS (Cloudflare Tunnel, Bearer <TOKEN>)
     │ └────────┴──────────┴────────┘  │         │
     │  StaticFiles  FastAPI  MCP      │         └── remote LLM clients (Cursor, LM Studio, OpenAI, opencode)
     └─────────────┬───────────────────┘
                   ▼
          paper_search_mcp library
```

One process, one port, one config file. Every surface reuses the same `paper-search-mcp` Python library, so connector logic is never duplicated.

## License

`paper-search-mcp` is MIT-licensed by its original authors. The backend, frontend, and scripts in this repo are MIT too.
