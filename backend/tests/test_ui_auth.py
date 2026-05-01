"""Unit tests for stateless UI session tokens (no full app import)."""

from __future__ import annotations

import unittest

from app.config import AppConfig, ServerConfig
from app.ui_auth import issue_ui_session_token, ui_session_token_valid


class TestUiSessionTokens(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = AppConfig(
            auth_token="test-mcp-token-for-signing",
            public_url="http://localhost:3636",
            server=ServerConfig(),
            raw={},
            ui_password="ui-secret",
            session_secret="",
        )

    def test_issue_and_validate(self) -> None:
        token = issue_ui_session_token(self.cfg)
        self.assertTrue(ui_session_token_valid(self.cfg, token))

    def test_reject_empty_and_tampered(self) -> None:
        self.assertFalse(ui_session_token_valid(self.cfg, None))
        self.assertFalse(ui_session_token_valid(self.cfg, ""))
        token = issue_ui_session_token(self.cfg)
        self.assertFalse(ui_session_token_valid(self.cfg, token + "x"))

    def test_different_password_changes_nothing_when_auth_token_set(self) -> None:
        """Signing key prefers ``auth_token`` over ``ui_password``."""
        other = AppConfig(
            auth_token=self.cfg.auth_token,
            public_url=self.cfg.public_url,
            server=self.cfg.server,
            raw={},
            ui_password="other-password",
            session_secret="",
        )
        token = issue_ui_session_token(self.cfg)
        self.assertTrue(ui_session_token_valid(other, token))


if __name__ == "__main__":
    unittest.main()
