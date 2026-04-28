"""Token manager — API key & OAuth storage.

Uses ``flet_secure_storage`` for encrypted persistent key-value storage.
"""

from __future__ import annotations

import logging
from typing import Optional

import flet as ft
import flet_secure_storage as fss

logger = logging.getLogger(__name__)

_API_KEY_SLOT = "fletbot_api_key"
_OAUTH_TOKEN_SLOT = "fletbot_oauth_token"


class TokenManager:
    """Manage the user's API key and OAuth token via flet_secure_storage."""

    def __init__(self, page: ft.Page):
        self._page = page
        self._storage = fss.SecureStorage()

    # ── API Key Methods ─────────────────────────────────────────────

    async def has_api_key(self) -> bool:
        """Check whether an API key is stored."""
        key = await self.get_api_key()
        return key is not None and len(key) > 0

    async def get_api_key(self) -> Optional[str]:
        """Retrieve the stored API key, or None."""
        try:
            return await self._storage.get(_API_KEY_SLOT)
        except Exception as e:
            logger.error("Failed to read API key: %s", e)
            return None

    async def save_api_key(self, key: str) -> None:
        """Store the API key securely."""
        try:
            await self._storage.set(_API_KEY_SLOT, key)
            logger.info("API key saved securely")
        except Exception as e:
            logger.error("Failed to save API key: %s", e)

    async def clear_api_key(self) -> None:
        """Remove the stored API key."""
        try:
            await self._storage.remove(_API_KEY_SLOT)
            logger.info("API key cleared")
        except Exception as e:
            logger.error("Failed to clear API key: %s", e)

    # ── OAuth Token Methods ─────────────────────────────────────────

    async def has_oauth_token(self) -> bool:
        """Check whether an OAuth token is stored."""
        token = await self.get_oauth_token()
        return token is not None and len(token) > 0

    async def get_oauth_token(self) -> Optional[str]:
        """Retrieve the stored OAuth token, or None."""
        try:
            return await self._storage.get(_OAUTH_TOKEN_SLOT)
        except Exception as e:
            logger.error("Failed to read OAuth token: %s", e)
            return None

    async def save_oauth_token(self, token: str) -> None:
        """Store the OAuth token securely."""
        try:
            await self._storage.set(_OAUTH_TOKEN_SLOT, token)
            logger.info("OAuth token saved securely")
        except Exception as e:
            logger.error("Failed to save OAuth token: %s", e)

    async def clear_oauth_token(self) -> None:
        """Remove the stored OAuth token."""
        try:
            await self._storage.remove(_OAUTH_TOKEN_SLOT)
            logger.info("OAuth token cleared")
        except Exception as e:
            logger.error("Failed to clear OAuth token: %s", e)
