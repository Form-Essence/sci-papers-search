"""Single source of truth: mcp-config.json at the repo root.

Loads the JSON, exposes a typed config object for our own code, and
populates ``os.environ`` with the ``PAPER_SEARCH_MCP_*`` keys that the
upstream ``paper_search_mcp`` library reads. Call ``load_config()`` BEFORE
importing ``paper_search_mcp`` so its ``get_env`` calls see the values.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = REPO_ROOT / "mcp-config.json"


def _config_path() -> Path:
    override = os.getenv("PAPER_SEARCH_CONFIG", "").strip()
    return Path(override).expanduser() if override else _DEFAULT_CONFIG_PATH


# Map ``server.api_keys.<cfg_key>`` -> env var the upstream library honors.
_API_KEY_ENV_MAP: dict[str, str] = {
    "unpaywall_email": "PAPER_SEARCH_MCP_UNPAYWALL_EMAIL",
    "core_api_key": "PAPER_SEARCH_MCP_CORE_API_KEY",
    "semantic_scholar_api_key": "PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY",
    "google_scholar_proxy_url": "PAPER_SEARCH_MCP_GOOGLE_SCHOLAR_PROXY_URL",
    "zenodo_access_token": "PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN",
    "doaj_api_key": "PAPER_SEARCH_MCP_DOAJ_API_KEY",
    "ieee_api_key": "PAPER_SEARCH_MCP_IEEE_API_KEY",
    "acm_api_key": "PAPER_SEARCH_MCP_ACM_API_KEY",
}


@dataclass(frozen=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 3636
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    per_source_timeout: float = 25.0


@dataclass(frozen=True)
class AppConfig:
    public_url: str
    server: ServerConfig
    raw: dict[str, Any]
    ui_password: str = ""
    session_secret: str = ""


_LOADED: AppConfig | None = None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}. Copy mcp-config.example.json to mcp-config.json."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path: Path | None = None, reload: bool = False) -> AppConfig:
    """Load mcp-config.json and propagate API keys into ``os.environ``.

    Safe to call many times; subsequent calls are no-ops unless ``reload=True``.
    """
    global _LOADED
    if _LOADED is not None and not reload:
        return _LOADED

    target = path or _config_path()
    data = _read_json(target)

    server_raw = data.get("server") or {}
    api_keys = server_raw.get("api_keys") or {}

    cors_origins = [
        str(o).strip()
        for o in (server_raw.get("cors_origins") or ["*"])
        if str(o).strip()
    ] or ["*"]

    cfg = AppConfig(
        public_url=(str(data.get("public_url") or "").strip() or "http://localhost:3636"),
        server=ServerConfig(
            host=str(server_raw.get("host") or "0.0.0.0"),
            port=int(server_raw.get("port") or 3636),
            cors_origins=cors_origins,
            per_source_timeout=float(server_raw.get("per_source_timeout") or 25.0),
        ),
        raw=data,
        ui_password=str(data.get("ui_password") or "").strip(),
        session_secret=str(data.get("session_secret") or "").strip(),
    )

    for cfg_key, env_name in _API_KEY_ENV_MAP.items():
        value = str(api_keys.get(cfg_key) or "").strip()
        if value:
            os.environ.setdefault(env_name, value)

    _LOADED = cfg
    logger.info("Loaded config from %s", target)
    return cfg
