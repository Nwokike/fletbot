"""Permission handling service.

Wraps ``flet-permission-handler`` to provide a clean async API
for requesting camera, microphone, and storage permissions.

API verified against flet-permission-handler v0.84.0:
- PermissionHandler().request(Permission.CAMERA) -> PermissionStatus
- Permission: CAMERA, MICROPHONE, STORAGE
- PermissionStatus: GRANTED, LIMITED, DENIED, PERMANENTLY_DENIED, etc.
"""

from __future__ import annotations

import logging
import sys

import flet as ft

logger = logging.getLogger(__name__)

# Permission handler is mobile-only; guard the import.
_HAS_HANDLER = False
try:
    from flet_permission_handler import (
        Permission,
        PermissionHandler,
        PermissionStatus,
    )

    _HAS_HANDLER = True
except ImportError:
    pass


def _is_desktop() -> bool:
    return sys.platform in ("win32", "linux", "darwin")


class PermissionService:
    """Unified permission requester for FletBot.

    On desktop the methods simply return ``True`` because native
    permissions don't apply.
    """

    def __init__(self, page: ft.Page):
        self._page = page
        self._handler: PermissionHandler | None = None
        if _HAS_HANDLER and not _is_desktop():
            self._handler = PermissionHandler()

    async def _request(self, perm: "Permission") -> bool:
        """Request a single permission; return True if granted."""
        if self._handler is None:
            return True  # Desktop — always allowed
        status = await self._handler.request(perm)
        granted = status in (
            PermissionStatus.GRANTED,
            PermissionStatus.LIMITED,
        )
        if not granted:
            logger.warning("Permission %s denied (status=%s)", perm, status)
        return granted

    async def request_camera(self) -> bool:
        if not _HAS_HANDLER or _is_desktop():
            return True
        return await self._request(Permission.CAMERA)

    async def request_microphone(self) -> bool:
        if not _HAS_HANDLER or _is_desktop():
            return True
        return await self._request(Permission.MICROPHONE)

    async def request_storage(self) -> bool:
        if not _HAS_HANDLER or _is_desktop():
            return True
        return await self._request(Permission.STORAGE)
