"""Token manager — API key storage.

Uses ``ft.SharedPreferences`` service for persistent key-value storage.
"""

from __future__ import annotations

import logging

import flet as ft

logger = logging.getLogger(__name__)

_API_KEY_SLOT = "fletbot_api_key"


class TokenManager:
    """Manage the user's API key via ft.SharedPreferences."""

    def __init__(self, page: ft.Page):
        self._page = page
        self._prefs = ft.SharedPreferences()

    async def has_api_key(self) -> bool:
        """Check whether an API key is stored."""
        key = await self.get_api_key()
        return key is not None and len(key) > 0

    async def get_api_key(self) -> str | None:
        """Retrieve the stored API key, or None."""
        try:
            return await self._prefs.get(_API_KEY_SLOT)
        except Exception as e:
            logger.error("Failed to read API key: %s", e)
            return None

    async def save_api_key(self, key: str) -> None:
        """Store the API key."""
        try:
            await self._prefs.set(_API_KEY_SLOT, key)
            logger.info("API key saved")
        except Exception as e:
            logger.error("Failed to save API key: %s", e)

    async def clear_api_key(self) -> None:
        """Remove the stored API key."""
        try:
            await self._prefs.remove(_API_KEY_SLOT)
            logger.info("API key cleared")
        except Exception as e:
            logger.error("Failed to clear API key: %s", e)
