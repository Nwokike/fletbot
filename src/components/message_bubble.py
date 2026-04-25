"""Message bubble component for the chat UI."""

from __future__ import annotations

import flet as ft

from src.components.markdown_renderer import MarkdownRenderer


class MessageBubble(ft.Container):
    """A chat message bubble.

    User messages: right-aligned, primary color.
    AI messages: left-aligned, surface variant, rendered as markdown.
    """

    def __init__(self, role: str, content: str, **kwargs):
        self._role = role
        self._content = content

        is_user = role == "user"

        # Build content based on role
        if is_user:
            display = ft.Text(
                content,
                color=ft.Colors.ON_PRIMARY,
                size=15,
                selectable=True,
            )
        else:
            display = MarkdownRenderer(content)

        # Role label
        role_label = ft.Text(
            "You" if is_user else "FletBot",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=(ft.Colors.ON_PRIMARY_CONTAINER if is_user else ft.Colors.PRIMARY),
        )

        bubble_content = ft.Column(
            controls=[role_label, display],
            spacing=4,
            tight=True,
        )

        super().__init__(
            content=bubble_content,
            bgcolor=(None if is_user else ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            gradient=(
                ft.LinearGradient(
                    begin=ft.Alignment.BOTTOM_LEFT,
                    end=ft.Alignment.TOP_RIGHT,
                    colors=["#00A859", "#008A49"],
                ) if is_user else None
            ),
            blur=(None if is_user else ft.Blur(10, 10, ft.BlurTileMode.MIRROR)),
            border=(None if is_user else ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))),
            border_radius=ft.border_radius.only(
                top_left=16,
                top_right=16,
                bottom_left=4 if is_user else 16,
                bottom_right=16 if is_user else 4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            margin=ft.margin.only(
                left=60 if is_user else 0,
                right=0 if is_user else 60,
                bottom=8,
            ),
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            shadow=(
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.2, "#00A859"),
                    offset=ft.Offset(0, 4),
                ) if is_user else ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 4),
                )
            ),
            **kwargs,
        )


class ThinkingIndicator(ft.Container):
    """A 'thinking' indicator shown while the AI is generating."""

    def __init__(self):
        super().__init__(
            content=ft.Row(
                controls=[
                    ft.ProgressRing(
                        width=16,
                        height=16,
                        stroke_width=2,
                        color=ft.Colors.PRIMARY,
                    ),
                    ft.Text(
                        "FletBot is thinking...",
                        size=13,
                        italic=True,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            margin=ft.margin.only(right=60, bottom=8),
        )
