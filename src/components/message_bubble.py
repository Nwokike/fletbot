"""Message bubble component for the chat UI.

Uses design system tokens for all visual styling.
"""

from __future__ import annotations

import flet as ft

from components.markdown_renderer import MarkdownRenderer
from theme import colors, tokens
from theme.styles import dark_shadow, primary_shadow


class MessageBubble(ft.Container):
    """A chat message bubble.

    User messages: right-aligned, Kiri Green gradient.
    AI messages: left-aligned, glassmorphic, rendered as markdown.
    """

    def __init__(self, role: str, content: str, on_copy=None, on_share=None, **kwargs):
        self._role = role
        self._content = content

        is_user = role == "user"

        # Build content based on role
        if is_user:
            display = ft.Text(
                content,
                color=ft.Colors.ON_PRIMARY,
                size=tokens.FONT_MD,
                selectable=True,
            )
        else:
            display = MarkdownRenderer(content)

        # Role label
        role_label = ft.Text(
            "You" if is_user else "FletBot",
            size=tokens.FONT_XXS,
            weight=ft.FontWeight.BOLD,
            color=(
                ft.Colors.ON_PRIMARY_CONTAINER if is_user else ft.Colors.PRIMARY
            ),
        )

        # Action buttons for AI messages
        action_row: list[ft.Control] = []
        if not is_user and content:
            if on_copy:
                action_row.append(
                    ft.IconButton(
                        icon=ft.Icons.COPY_ROUNDED,
                        icon_size=tokens.ICON_SM,
                        icon_color=ft.Colors.ON_SURFACE_VARIANT,
                        tooltip="Copy",
                        on_click=lambda _: on_copy(content),
                    )
                )
            if on_share:
                action_row.append(
                    ft.IconButton(
                        icon=ft.Icons.SHARE_ROUNDED,
                        icon_size=tokens.ICON_SM,
                        icon_color=ft.Colors.ON_SURFACE_VARIANT,
                        tooltip="Share",
                        on_click=lambda _: on_share(content),
                    )
                )

        bubble_controls: list[ft.Control] = [role_label, display]
        if action_row:
            bubble_controls.append(
                ft.Row(
                    controls=action_row,
                    spacing=0,
                    alignment=ft.MainAxisAlignment.END,
                )
            )

        bubble_content = ft.Column(
            controls=bubble_controls,
            spacing=tokens.SPACE_XS,
            tight=True,
        )

        super().__init__(
            content=bubble_content,
            bgcolor=(None if is_user else colors.GLASS_BG),
            gradient=(colors.user_bubble_gradient() if is_user else None),
            blur=(
                None
                if is_user
                else ft.Blur(tokens.BLUR_SM, tokens.BLUR_SM, ft.BlurTileMode.MIRROR)
            ),
            border=(
                None
                if is_user
                else ft.Border.all(1, colors.GLASS_BORDER_COLOR)
            ),
            border_radius=ft.BorderRadius.only(
                top_left=tokens.RADIUS_LG,
                top_right=tokens.RADIUS_LG,
                bottom_left=tokens.RADIUS_XS if is_user else tokens.RADIUS_LG,
                bottom_right=tokens.RADIUS_LG if is_user else tokens.RADIUS_XS,
            ),
            padding=ft.Padding.symmetric(
                horizontal=tokens.SPACE_LG, vertical=tokens.SPACE_SM + 2
            ),
            margin=ft.Margin.only(
                left=tokens.BUBBLE_INDENT if is_user else 0,
                right=0 if is_user else tokens.BUBBLE_INDENT,
                bottom=tokens.SPACE_SM,
            ),
            animate_opacity=ft.Animation(
                tokens.ANIMATION_MS, ft.AnimationCurve.EASE_OUT
            ),
            shadow=(primary_shadow() if is_user else dark_shadow()),
            **kwargs,
        )


class ThinkingIndicator(ft.Container):
    """A 'thinking' indicator shown while the AI is generating."""

    def __init__(self):
        super().__init__(
            content=ft.Row(
                controls=[
                    ft.ProgressRing(
                        width=tokens.ICON_SM - 2,
                        height=tokens.ICON_SM - 2,
                        stroke_width=tokens.PROGRESS_STROKE,
                        color=ft.Colors.PRIMARY,
                    ),
                    ft.Text(
                        "FletBot is thinking...",
                        size=tokens.FONT_SM,
                        italic=True,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=tokens.SPACE_SM + 2,
            ),
            padding=ft.Padding.symmetric(
                horizontal=tokens.SPACE_LG, vertical=tokens.SPACE_SM + 2
            ),
            margin=ft.Margin.only(
                right=tokens.BUBBLE_INDENT, bottom=tokens.SPACE_SM
            ),
        )
