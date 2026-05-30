"""Builders for client setup snippets shown in the UI's Connect modal.

Each builder returns an :class:`McpClientSnippet` whose ``snippet`` field is a
copy-paste-ready string for the corresponding MCP client. Snippets are derived
from ``mcp-config.json`` (``public_url``) so moving the deployment only
requires editing that one file.
"""

from __future__ import annotations

import json

from .schemas import McpClientSnippet, McpConfigResponse


def _pretty_json(payload: dict) -> str:
    return json.dumps(payload, indent=2)


def _cursor(mcp_url: str) -> McpClientSnippet:
    snippet = _pretty_json(
        {
            "mcpServers": {
                "paper-search": {
                    "url": mcp_url,
                }
            }
        }
    )
    return McpClientSnippet(
        id="cursor",
        label="Cursor",
        language="json",
        filename="~/.cursor/mcp.json",
        instructions=(
            "Open Cursor settings (or edit ~/.cursor/mcp.json) and merge the "
            "snippet below into your existing mcpServers map. Restart Cursor "
            "to pick up the change."
        ),
        snippet=snippet,
    )


def _claude_code(mcp_url: str) -> McpClientSnippet:
    cmd = f"claude mcp add --transport http paper-search {mcp_url}"
    return McpClientSnippet(
        id="claude_code",
        label="Claude Code",
        language="bash",
        filename=None,
        instructions=(
            "Run this once in your terminal. Claude Code stores the server in "
            "its user-level MCP config; verify with `claude mcp list`."
        ),
        snippet=cmd,
    )


def _claude_desktop(mcp_url: str) -> McpClientSnippet:
    snippet = _pretty_json(
        {
            "mcpServers": {
                "paper-search": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "mcp-remote",
                        mcp_url,
                    ],
                }
            }
        }
    )
    return McpClientSnippet(
        id="claude_desktop",
        label="Claude Desktop",
        language="json",
        filename="claude_desktop_config.json",
        instructions=(
            "Claude Desktop currently speaks stdio, not streamable HTTP, so "
            "the snippet uses the mcp-remote bridge (npx will fetch it on "
            "first run). Merge into claude_desktop_config.json and restart "
            "Claude Desktop."
        ),
        snippet=snippet,
    )


def _opencode(mcp_url: str) -> McpClientSnippet:
    snippet = _pretty_json(
        {
            "mcp": {
                "paper-search": {
                    "type": "remote",
                    "url": mcp_url,
                    "enabled": True,
                }
            }
        }
    )
    return McpClientSnippet(
        id="opencode",
        label="OpenCode",
        language="json",
        filename="opencode.json",
        instructions=(
            "Add to your project's opencode.json (or the user-level config). "
            "OpenCode connects on next launch."
        ),
        snippet=snippet,
    )


def _lm_studio(mcp_url: str) -> McpClientSnippet:
    snippet = _pretty_json(
        {
            "mcpServers": {
                "paper-search": {
                    "url": mcp_url,
                }
            }
        }
    )
    return McpClientSnippet(
        id="lm_studio",
        label="LM Studio",
        language="json",
        filename="mcp.json",
        instructions=(
            "In LM Studio open the MCP panel and edit mcp.json. Merge the "
            "snippet into the mcpServers map, then toggle the server on."
        ),
        snippet=snippet,
    )


def _openai(mcp_url: str) -> McpClientSnippet:
    snippet = _pretty_json(
        {
            "tools": [
                {
                    "type": "mcp",
                    "server_label": "paper-search",
                    "server_url": mcp_url,
                    "require_approval": "never",
                }
            ]
        }
    )
    return McpClientSnippet(
        id="openai_responses",
        label="OpenAI",
        language="json",
        filename=None,
        instructions=(
            "Pass this tools array when calling the OpenAI Responses API. "
            "The model will be able to call paper-search tools directly."
        ),
        snippet=snippet,
    )


def build_client_snippets(*, public_url: str, mcp_url: str) -> McpConfigResponse:
    builders = (
        _cursor,
        _claude_code,
        _claude_desktop,
        _opencode,
        _lm_studio,
        _openai,
    )
    clients = [build(mcp_url) for build in builders]
    return McpConfigResponse(
        public_url=public_url,
        mcp_url=mcp_url,
        clients=clients,
    )
