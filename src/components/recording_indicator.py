"""Recording indicator component for audio recording UI."""

import asyncio
from typing import Callable

import flet as ft

from theme import tokens, colors

class RecordingIndicator(ft.Container):
    """Replaces text input while recording. Shows timer and pulsing mic."""

    def __init__(self, page: ft.Page, on_stop: Callable[[], None], max_duration: int = 300):
        self._page = page
        self._on_stop = on_stop
        self._max_duration = max_duration
        self._elapsed = 0
        self._is_running = False
        
        self._timer_text = ft.Text(
            "00:00",
            size=tokens.FONT_MD,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.ERROR
        )

        self._mic_icon = ft.Icon(
            ft.Icons.MIC_ROUNDED,
            color=ft.Colors.ERROR,
            size=tokens.ICON_MD,
        )

        self._stop_btn = ft.IconButton(
            icon=ft.Icons.STOP_CIRCLE_ROUNDED,
            icon_color=ft.Colors.ERROR,
            icon_size=32,
            tooltip="Stop recording",
            on_click=self._handle_stop,
            style=ft.ButtonStyle(padding=0),
        )

        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            self._mic_icon,
                            ft.Text("Recording...", size=tokens.FONT_MD, color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=tokens.SPACE_XS,
                    ),
                    ft.Row(
                        controls=[
                            self._timer_text,
                            ft.Container(width=tokens.SPACE_SM),
                            self._stop_btn,
                        ],
                        spacing=tokens.SPACE_XS,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=tokens.SPACE_LG, vertical=tokens.SPACE_SM + 2),
            expand=True,
            visible=False,
        )

    def start(self):
        """Start the recording timer and animation."""
        self._elapsed = 0
        self._is_running = True
        self.visible = True
        self._update_timer_text()
        self.update()
        
        # Start background tasks
        self._page.run_task(self._timer_loop)
        self._page.run_task(self._pulse_loop)

    def stop(self):
        """Stop the recording UI."""
        self._is_running = False
        self.visible = False
        self.update()

    def _handle_stop(self, e):
        self._on_stop()

    async def _timer_loop(self):
        """Update timer every second and handle auto-stop."""
        while self._is_running and self._elapsed < self._max_duration:
            await asyncio.sleep(1)
            if not self._is_running:
                break
            self._elapsed += 1
            self._update_timer_text()
            self.update()

        if self._is_running and self._elapsed >= self._max_duration:
            self._on_stop()

    async def _pulse_loop(self):
        """Pulse the mic icon."""
        scale_up = True
        while self._is_running:
            self._mic_icon.scale = 1.2 if scale_up else 1.0
            self._mic_icon.update()
            scale_up = not scale_up
            await asyncio.sleep(0.5)
        
        # Reset scale when stopped
        try:
            self._mic_icon.scale = 1.0
            self._mic_icon.update()
        except Exception:
            pass

    def _update_timer_text(self):
        mins, secs = divmod(self._elapsed, 60)
        self._timer_text.value = f"{mins:02d}:{secs:02d}"
