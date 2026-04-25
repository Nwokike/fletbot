"""Token manager — secure storage for API keys and auth tokens."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Key names in secure/client storage
_API_KEY_SLOT = "fletbot.api_key"
_USER_NAME_SLOT = "fletbot.user_name"


class TokenManager:
    """Manages API key storage using Flet's client_storage (SharedPreferences).

    For MVP we use client_storage which is available on all platforms.
    In production, migrate to flet-secure-storage for encrypted storage.
    """

    def __init__(self, page):
        self._page = page

    async def save_api_key(self, key: str) -> None:
        """Store the Google AI Studio API key."""
        await self._page.shared_preferences.set(_API_KEY_SLOT, key)
        logger.info("API key saved to client storage")

    async def get_api_key(self) -> Optional[str]:
        """Retrieve the stored API key, or None if not set."""
        try:
            return await self._page.shared_preferences.get(_API_KEY_SLOT)
        except Exception:
            return None

    async def has_api_key(self) -> bool:
        """Check if an API key is stored."""
        key = await self.get_api_key()
        return key is not None and len(key) > 0

    async def clear_api_key(self) -> None:
        """Remove the stored API key."""
        try:
            await self._page.shared_preferences.remove(_API_KEY_SLOT)
        except Exception:
            pass
        logger.info("API key cleared from client storage")

    async def save_user_name(self, name: str) -> None:
        """Store a display name for the user."""
        await self._page.shared_preferences.set(_USER_NAME_SLOT, name)

    async def get_user_name(self) -> Optional[str]:
        """Retrieve the stored user name."""
        try:
            return await self._page.shared_preferences.get(_USER_NAME_SLOT)
        except Exception:
            return None
