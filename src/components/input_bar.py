"""Input bar component for the chat UI.

Uses design system tokens and wires camera, mic, and file attach buttons
to the native service layer.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import flet as ft

from theme import colors, tokens

logger = logging.getLogger(__name__)


class InputBar(ft.Container):
    """Chat input bar with text field, send button, and native action buttons.

    Supports submit on Enter, Shift+Enter for newline.
    Camera, mic, and attach buttons are wired to real native services.
    """

    def __init__(
        self,
        page: ft.Page,
        on_send: Optional[Callable[[str], None]] = None,
        on_camera: Optional[Callable[[], None]] = None,
        on_mic: Optional[Callable[[], None]] = None,
        on_attach: Optional[Callable[[], None]] = None,
        disabled: bool = False,
    ):
        self._page = page
        self._on_send = on_send
        self._disabled = disabled

        self._text_field = ft.TextField(
            hint_text="Ask FletBot anything...",
            border_radius=tokens.RADIUS_XXL,
            filled=True,
            dense=True,
            min_lines=1,
            max_lines=5,
            multiline=True,
            shift_enter=True,
            on_submit=self._handle_submit,
            expand=True,
            text_size=tokens.FONT_MD,
            content_padding=ft.Padding.symmetric(
                horizontal=tokens.SPACE_LG, vertical=tokens.SPACE_SM + 2
            ),
            disabled=disabled,
        )

        self._send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_color=ft.Colors.ON_PRIMARY,
            bgcolor=ft.Colors.PRIMARY,
            on_click=self._handle_click,
            disabled=disabled,
            tooltip="Send message",
            icon_size=tokens.ICON_MD,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=tokens.SPACE_SM + 2,
            ),
        )

        self._camera_btn = ft.IconButton(
            icon=ft.Icons.CAMERA_ALT_ROUNDED,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            tooltip="Use Camera (Photo/Video)",
            on_click=lambda _: on_camera() if on_camera else None,
            icon_size=tokens.ICON_MD,
        )
        self._mic_btn = ft.IconButton(
            icon=ft.Icons.MIC_ROUNDED,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            tooltip="Record audio",
            on_click=lambda _: on_mic() if on_mic else None,
            icon_size=tokens.ICON_MD,
        )
        self._attach_btn = ft.IconButton(
            icon=ft.Icons.ATTACH_FILE_ROUNDED,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            tooltip="Attach document",
            on_click=lambda _: on_attach() if on_attach else None,
            icon_size=tokens.ICON_MD,
        )

        from components.recording_indicator import RecordingIndicator

        self._normal_input = ft.Row(
            controls=[
                self._attach_btn,
                self._camera_btn,
                self._mic_btn,
                self._text_field,
                self._send_button,
            ],
            spacing=tokens.SPACE_XS,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )

        def _handle_stop_recording():
            self.set_recording(False)
            if on_mic:
                # Signal stop
                on_mic(stopped=True)
                
        self._recording_indicator = RecordingIndicator(page=self._page, on_stop=_handle_stop_recording, max_duration=300)

        super().__init__(
            content=ft.Stack(
                controls=[
                    self._normal_input,
                    self._recording_indicator,
                ]
            ),
            padding=ft.Padding.only(
                left=tokens.SPACE_SM,
                right=tokens.SPACE_SM,
                top=tokens.INPUT_BAR_HEIGHT,
                bottom=tokens.INPUT_BAR_HEIGHT,
            ),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.SURFACE),
            blur=ft.Blur(
                tokens.BLUR_MD, tokens.BLUR_MD, ft.BlurTileMode.MIRROR
            ),
            border_radius=ft.BorderRadius.only(
                top_left=tokens.RADIUS_XXL, top_right=tokens.RADIUS_XXL
            ),
            border=ft.Border.all(1, colors.GLASS_BORDER_COLOR),
        )

    def _handle_submit(self, e):
        """Handle Enter key press."""
        self._send_current()

    def _handle_click(self, e):
        """Handle send button click."""
        self._send_current()

    def _send_current(self):
        """Send the current text if not empty (or if media is attached, handled upstream)."""
        text = self._text_field.value
        if self._on_send:
            self._on_send(text.strip() if text else "")
            self._text_field.value = ""
            self._text_field.update()

    def set_disabled(self, disabled: bool):
        """Enable or disable the input bar."""
        self._disabled = disabled
        self._text_field.disabled = disabled
        self._send_button.disabled = disabled
        self.update()

    def set_recording(self, recording: bool):
        """Toggle between text input and recording UI."""
        if recording:
            self._normal_input.visible = False
            self._recording_indicator.start()
        else:
            self._recording_indicator.stop()
            self._normal_input.visible = True
        self.update()

    def focus(self):
        """Focus the text field."""
        self._text_field.focus()
