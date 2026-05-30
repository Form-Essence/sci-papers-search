"""Unit tests for stateless UI session tokens (no full app import)."""

from __future__ import annotations

import unittest

from app.config import AppConfig, ServerConfig
from app.ui_auth import issue_ui_session_token, ui_session_token_valid


class TestUiSessionTokens(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = AppConfig(
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

    def test_session_secret_isolates_signing_key(self) -> None:
        """Signing key uses ``session_secret`` when set, else falls back to ``ui_password``."""
        cfg_with_secret = AppConfig(
            public_url=self.cfg.public_url,
            server=self.cfg.server,
            raw={},
            ui_password="other-password",
            session_secret="shared-secret",
        )
        cfg_same_secret = AppConfig(
            public_url=self.cfg.public_url,
            server=self.cfg.server,
            raw={},
            ui_password="yet-another-password",
            session_secret="shared-secret",
        )
        token = issue_ui_session_token(cfg_with_secret)
        self.assertTrue(ui_session_token_valid(cfg_same_secret, token))


if __name__ == "__main__":
    unittest.main()
