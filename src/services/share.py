"""Share and clipboard service.

Provides copy-to-clipboard and native share-sheet functionality.
"""

from __future__ import annotations

import logging

import flet as ft

logger = logging.getLogger(__name__)


class ShareService:
    """Clipboard and share helper."""

    def __init__(self, page: ft.Page):
        self._page = page

    async def copy_text(self, text: str) -> None:
        """Copy text to the system clipboard."""
        await self._page.clipboard.set(text)
        self._page.show_dialog(
            ft.SnackBar(
                content=ft.Text("Copied to clipboard ✓"),
                duration=1500,
            )
        )
        logger.info("Copied %d chars to clipboard", len(text))

    def share_text(self, text: str) -> None:
        """Open the native share sheet with the given text."""
        try:
            self._page.launch_url(
                f"https://wa.me/?text={text[:500]}"  # Fallback to WhatsApp
            )
        except Exception:
            # Clipboard fallback if share isn't available
            self._page.run_task(self.copy_text, text)
