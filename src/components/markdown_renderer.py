"""Markdown renderer — configurable wrapper around ft.Markdown.

Provides a consistent, styled Markdown rendering component for
AI responses, with code syntax highlighting and link handling.
"""

from __future__ import annotations

import flet as ft


class MarkdownRenderer(ft.Markdown):
    """Styled Markdown renderer for AI responses.

    Wraps ft.Markdown with sensible defaults for consumer chat:
    - GitHub-flavored markdown extensions
    - Code syntax highlighting
    - Clickable links (open in browser)
    - Selectable text
    - Responsive fit
    """

    def __init__(self, content: str = "", **kwargs):
        super().__init__(
            value=content,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme=ft.MarkdownCodeTheme.MONOKAI,
            auto_follow_links=True,
            fit_content=True,
            code_style_sheet=ft.MarkdownStyleSheet(
                code_text_style=ft.TextStyle(
                    font_family="Roboto Mono",
                    size=13,
                ),
            ),
            **kwargs,
        )

    def update_content(self, new_content: str):
        """Update the displayed markdown content."""
        self.value = new_content
        self.update()
