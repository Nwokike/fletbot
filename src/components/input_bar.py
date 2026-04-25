"""Input bar component for the chat UI."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft


class InputBar(ft.Container):
    """Chat input bar with text field and send button.

    Supports submit on Enter, Shift+Enter for newline.
    """

    def __init__(
        self,
        on_send: Optional[Callable[[str], None]] = None,
        disabled: bool = False,
    ):
        self._on_send = on_send
        self._disabled = disabled

        self._text_field = ft.TextField(
            hint_text="Ask FletBot anything...",
            border_radius=24,
            filled=True,
            dense=True,
            min_lines=1,
            max_lines=5,
            multiline=True,
            shift_enter=True,
            on_submit=self._handle_submit,
            expand=True,
            text_size=15,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=10),
            disabled=disabled,
        )

        self._send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_color=ft.Colors.ON_PRIMARY,
            bgcolor=ft.Colors.PRIMARY,
            on_click=self._handle_click,
            disabled=disabled,
            tooltip="Send message",
            icon_size=20,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=10,
            ),
        )

        self._camera_btn = ft.IconButton(
            icon=ft.Icons.CAMERA_ALT_ROUNDED,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            tooltip="Take photo",
        )
        self._mic_btn = ft.IconButton(
            icon=ft.Icons.MIC_ROUNDED,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            tooltip="Record audio",
        )
        self._attach_btn = ft.IconButton(
            icon=ft.Icons.ATTACH_FILE_ROUNDED,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            tooltip="Attach document",
        )

        super().__init__(
            content=ft.Row(
                controls=[
                    self._attach_btn,
                    self._camera_btn,
                    self._mic_btn,
                    self._text_field,
                    self._send_button
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            padding=ft.padding.only(left=8, right=8, top=12, bottom=12),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.SURFACE),
            blur=ft.Blur(20, 20, ft.BlurTileMode.MIRROR),
            border_radius=ft.border_radius.only(top_left=24, top_right=24),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
        )

    def _handle_submit(self, e):
        """Handle Enter key press."""
        self._send_current()

    def _handle_click(self, e):
        """Handle send button click."""
        self._send_current()

    def _send_current(self):
        """Send the current text if not empty."""
        text = self._text_field.value
        if text and text.strip() and self._on_send:
            self._on_send(text.strip())
            self._text_field.value = ""
            self._text_field.update()

    def set_disabled(self, disabled: bool):
        """Enable or disable the input bar."""
        self._disabled = disabled
        self._text_field.disabled = disabled
        self._send_button.disabled = disabled
        self.update()

    def focus(self):
        """Focus the text field."""
        self._text_field.focus()
