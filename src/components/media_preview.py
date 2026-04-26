"""Media preview staging area.

Displays selected files, photos, or voice notes above the input bar before sending.
"""

from typing import Callable, Optional

import flet as ft

from src.providers.base import MediaPart
from src.theme import tokens, colors

class MediaPreviewBar(ft.Container):
    """Bar displaying pending media items."""

    def __init__(self, on_remove: Callable[[MediaPart], None]):
        self._on_remove = on_remove
        self._items = ft.Row(spacing=tokens.SPACE_SM, scroll=ft.ScrollMode.ADAPTIVE)
        
        super().__init__(
            content=self._items,
            padding=ft.Padding.only(left=tokens.SPACE_MD, right=tokens.SPACE_MD, top=tokens.SPACE_SM),
            visible=False,
            animate_opacity=ft.Animation(tokens.ANIMATION_MS, ft.AnimationCurve.EASE_OUT),
        )

    def set_media(self, media_parts: list[MediaPart]):
        """Update the displayed media."""
        self._items.controls.clear()
        
        for part in media_parts:
            # Determine icon based on mime type
            icon = ft.Icons.INSERT_DRIVE_FILE_ROUNDED
            if part.mime_type.startswith("image/"):
                icon = ft.Icons.IMAGE_ROUNDED
            elif part.mime_type.startswith("video/"):
                icon = ft.Icons.VIDEO_FILE_ROUNDED
            elif part.mime_type.startswith("audio/"):
                icon = ft.Icons.MIC_ROUNDED
                
            label = part.filename or ("Voice Note" if part.mime_type.startswith("audio/") else "Attachment")

            chip = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon, size=16, color=ft.Colors.PRIMARY),
                        ft.Text(label, size=tokens.FONT_SM, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE_ROUNDED,
                            icon_size=14,
                            width=24,
                            height=24,
                            style=ft.ButtonStyle(padding=0),
                            on_click=self._make_remove_handler(part),
                        )
                    ],
                    spacing=tokens.SPACE_XS,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=tokens.SPACE_SM, vertical=4),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY),
                border_radius=tokens.RADIUS_MD,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY)),
            )
            self._items.controls.append(chip)

        self.visible = len(media_parts) > 0
        self.update()

    def _make_remove_handler(self, part: MediaPart):
        def handler(e):
            self._on_remove(part)
        return handler
