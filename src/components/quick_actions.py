"""Quick-action chip components for the chat welcome screen.

Reusable suggestion chips styled via the design system.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from theme import tokens
from theme.styles import chip_button_style


class QuickActionChip(ft.Button):
    """A single quick-action suggestion chip."""

    def __init__(self, label: str, prompt: str, on_send: Callable[[str], None]):
        super().__init__(
            content=ft.Text(label, size=tokens.FONT_SM),
            on_click=lambda _: on_send(prompt),
            style=chip_button_style(),
        )


class QuickActionRow(ft.Row):
    """A wrapped row of quick-action chips."""

    _SUGGESTIONS = [
        ("Explain quantum computing", "Explain quantum computing in simple terms"),
        ("Write a poem", "Write a short poem about the ocean"),
        ("Help me cook dinner", "Suggest a quick dinner recipe with chicken"),
        ("Translate to French", "Translate 'Hello, how are you today?' to French"),
        ("Summarise a topic", "Give me a brief summary of climate change"),
        ("Write an email", "Write a professional email declining a meeting invitation"),
    ]

    def __init__(self, on_send: Callable[[str], None]):
        chips = [
            QuickActionChip(label=label, prompt=prompt, on_send=on_send)
            for label, prompt in self._SUGGESTIONS
        ]
        super().__init__(
            controls=chips,
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True,
            spacing=tokens.SPACE_SM,
            run_spacing=tokens.SPACE_SM,
        )
