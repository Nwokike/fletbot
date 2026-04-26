"""History view — list of past conversations.

Uses design system tokens for all visual styling.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

import flet as ft

from session.manager import SessionManager
from theme import tokens
from theme.styles import brand_gradient_bg, standard_appbar

logger = logging.getLogger(__name__)


def _format_time(timestamp: float) -> str:
    """Format a timestamp into a human-readable relative time."""
    now = time.time()
    delta = now - timestamp

    if delta < 60:
        return "Just now"
    elif delta < 3600:
        mins = int(delta / 60)
        return f"{mins}m ago"
    elif delta < 86400:
        hours = int(delta / 3600)
        return f"{hours}h ago"
    else:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%b %d")


def build_history_view(
    page: ft.Page,
    session_manager: SessionManager,
    on_select_session: callable,
    on_back: callable,
) -> ft.View:
    """Build the conversation history view."""

    sessions = session_manager.list_sessions()

    def on_session_tap(session_id: str):
        def handler(e):
            on_select_session(session_id)

        return handler

    def on_delete_session(session_id: str):
        def handler(e):
            session_manager.delete_session(session_id)
            page.views[-1] = build_history_view(
                page, session_manager, on_select_session, on_back
            )
            page.update()

        return handler

    # Build session tiles
    tiles = []
    for session in sessions:
        if session.message_count == 0:
            continue

        tile = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
                            size=tokens.ICON_MD,
                            color=ft.Colors.PRIMARY,
                        ),
                        width=tokens.ICON_XL,
                        height=tokens.ICON_XL,
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        border_radius=tokens.RADIUS_XL,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                session.title,
                                size=tokens.FONT_MD,
                                weight=ft.FontWeight.W_500,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                f"{session.message_count} messages · {_format_time(session.updated_at)}",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=tokens.SPACE_XXS,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        icon_size=tokens.ICON_SM,
                        icon_color=ft.Colors.ERROR,
                        tooltip="Delete",
                        on_click=on_delete_session(session.id),
                    ),
                ],
                spacing=tokens.SPACE_MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(
                horizontal=tokens.SPACE_LG, vertical=tokens.SPACE_MD
            ),
            border_radius=tokens.RADIUS_MD,
            ink=True,
            on_click=on_session_tap(session.id),
        )
        tiles.append(tile)

    # Empty state
    if not tiles:
        content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.CHAT_OUTLINED,
                        size=tokens.ICON_LOGO,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        "No conversations yet",
                        size=tokens.FONT_LG,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        "Start a new chat to begin!",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.SPACE_SM,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
    else:
        content = ft.ListView(
            controls=tiles,
            expand=True,
            spacing=tokens.SPACE_XS,
            padding=ft.Padding.symmetric(
                horizontal=tokens.SPACE_MD, vertical=tokens.SPACE_SM
            ),
        )

    appbar = standard_appbar(
        "History",
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            tooltip="Back",
            on_click=lambda e: on_back(),
        ),
        transparent=True,
    )

    gradient_bg = brand_gradient_bg(content, page=page)

    view = ft.View(
        route="/history",
        controls=[gradient_bg],
        appbar=appbar,
        padding=0,
    )

    return view
