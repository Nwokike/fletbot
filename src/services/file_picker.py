"""File picker service.

Wraps ``ft.FilePicker`` to provide a clean async API for picking files.
Returns raw file bytes for multimodal AI input.

API verified against Flet v0.84.0:
- FilePicker() no longer takes on_result in constructor.
- pick_files() is an async method that returns list[FilePickerFile] directly.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import flet as ft

logger = logging.getLogger(__name__)


class FilePickerService:
    """File picker helper.

    Simplifies the flow of picking a file and reading its content as bytes.
    """

    def __init__(self, page: ft.Page, on_result: Callable[[bytes, str, str], None]):
        self._page = page
        self._on_result = on_result

        # Initialize the picker service (In 0.84.0+ it is a Service, not a control)
        self._picker = ft.FilePicker()

    def pick_file(self, allowed_extensions: Optional[list[str]] = None):
        """Trigger the file picker dialog."""
        # We run this as a task since pick_files is async in 0.84.0
        self._page.run_task(self._run_picker, allowed_extensions)

    async def _run_picker(self, allowed_extensions: Optional[list[str]] = None):
        """Async picker logic for Flet 0.84.0+."""
        try:
            # In 0.84.0+, pick_files returns the result directly
            result = await self._picker.pick_files(
                allowed_extensions=allowed_extensions,
                allow_multiple=False,
                with_data=True,  # Crucial: get file bytes directly
            )

            if result and len(result) > 0:
                file = result[0]
                # We expect data to be present because with_data=True
                if file.bytes:
                    # Heuristic for mime-type based on extension if not provided
                    mime = "application/octet-stream"
                    ext = file.name.split(".")[-1].lower() if "." in file.name else ""
                    if ext in ("jpg", "jpeg"):
                        mime = "image/jpeg"
                    elif ext == "png":
                        mime = "image/png"
                    elif ext == "pdf":
                        mime = "application/pdf"
                    elif ext == "txt":
                        mime = "text/plain"

                    self._on_result(file.bytes, mime, file.name)
                else:
                    logger.warning("File picked but no data returned (with_data=True failed?)")
            else:
                logger.info("File picking cancelled by user")

        except Exception as e:
            logger.error("File picking failed: %s", e)
            self._page.show_dialog(
                ft.SnackBar(content=ft.Text(f"File picker error: {e}"))
            )
