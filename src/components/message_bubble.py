"""Message bubble component for the chat UI.

Uses design system tokens for all visual styling.
"""

from __future__ import annotations

import flet as ft
import base64
from datetime import datetime

from src.components.markdown_renderer import MarkdownRenderer
from src.theme import colors, tokens
from src.theme.styles import dark_shadow, primary_shadow
from src.providers.base import MediaPart

class MessageBubble(ft.Container):
    """A chat message bubble.

    User messages: right-aligned, Kiri Green gradient.
    AI messages: left-aligned, glassmorphic, rendered as markdown.
    """

    def __init__(self, role: str, content: str, timestamp: str | None = None, on_copy=None, on_share=None, media: list[MediaPart] | None = None, **kwargs):
        self._role = role
        self._content = content
        self._timestamp = timestamp or datetime.now().strftime("%H:%M")

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

        bubble_controls: list[ft.Control] = [role_label]

        # Render Media if provided
        if media:
            media_controls = []
            for item in media:
                if item.mime_type.startswith("image/"):
                    b64_data = base64.b64encode(item.data).decode("utf-8")
                    media_controls.append(
                        ft.Container(
                            content=ft.Image(
                                src=f"data:{item.mime_type};base64,{b64_data}",
                                fit=ft.BoxFit.CONTAIN,
                            ),
                            border_radius=tokens.RADIUS_MD,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            height=150,
                        )
                    )
                else:
                    icon = ft.Icons.MIC if item.mime_type.startswith("audio/") else ft.Icons.INSERT_DRIVE_FILE
                    if item.mime_type.startswith("video/"):
                        icon = ft.Icons.VIDEOCAM
                    filename = item.filename or ("Voice Note" if item.mime_type.startswith("audio/") else "Attachment")
                    media_controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(icon, size=16, color=ft.Colors.ON_SURFACE_VARIANT if not is_user else ft.Colors.ON_PRIMARY),
                                ft.Text(filename, size=12, color=ft.Colors.ON_SURFACE_VARIANT if not is_user else ft.Colors.ON_PRIMARY)
                            ], tight=True),
                            padding=tokens.SPACE_XS,
                            bgcolor=ft.Colors.SURFACE_VARIANT if not is_user else "#33FFFFFF",
                            border_radius=tokens.RADIUS_SM,
                        )
                    )
            if media_controls:
                bubble_controls.append(ft.Column(controls=media_controls, spacing=tokens.SPACE_XS))

        if content:
            bubble_controls.append(display)

        # Bottom row: Timestamp + Actions
        bottom_row: list[ft.Control] = []
        
        # Timestamp
        bottom_row.append(
            ft.Text(
                self._timestamp,
                size=tokens.FONT_XXS - 2,
                color=ft.Colors.with_opacity(0.6, ft.Colors.ON_PRIMARY if is_user else ft.Colors.ON_SURFACE_VARIANT),
            )
        )
        
        # Action buttons for AI messages
        action_row: list[ft.Control] = []
        if not is_user and content:
            if on_copy:
                action_row.append(
                    ft.IconButton(
                        icon=ft.Icons.COPY_ROUNDED,
                        icon_size=tokens.ICON_SM - 2,
                        icon_color=ft.Colors.ON_SURFACE_VARIANT,
                        tooltip="Copy",
                        on_click=lambda _: on_copy(content),
                    )
                )
            if on_share:
                action_row.append(
                    ft.IconButton(
                        icon=ft.Icons.SHARE_ROUNDED,
                        icon_size=tokens.ICON_SM - 2,
                        icon_color=ft.Colors.ON_SURFACE_VARIANT,
                        tooltip="Share",
                        on_click=lambda _: on_share(content),
                    )
                )

        bottom_controls = ft.Row(
            controls=[
                bottom_row[0], # Timestamp
                ft.Row(controls=action_row, spacing=0) if action_row else ft.Container()
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            tight=True,
        )

        bubble_controls.append(bottom_controls)

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
            opacity=0,
            animate_opacity=ft.Animation(
                tokens.ANIMATION_MS, ft.AnimationCurve.EASE_OUT
            ),
            shadow=(primary_shadow() if is_user else dark_shadow()),
            on_animation_end=None,
            **kwargs,
        )

    def did_mount(self):
        self.opacity = 1
        self.update()


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
