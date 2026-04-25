"""History view — list of past conversations."""

from __future__ import annotations

import logging
import time
from datetime import datetime

import flet as ft

from src.session.manager import SessionManager

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
            # Rebuild view
            page.views[-1] = build_history_view(page, session_manager, on_select_session, on_back)
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
                            size=20,
                            color=ft.Colors.PRIMARY,
                        ),
                        width=40,
                        height=40,
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        border_radius=20,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                session.title,
                                size=15,
                                weight=ft.FontWeight.W_500,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                f"{session.message_count} messages · {_format_time(session.updated_at)}",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        icon_size=18,
                        icon_color=ft.Colors.ERROR,
                        tooltip="Delete",
                        on_click=on_delete_session(session.id),
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=12,
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
                        size=64,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        "No conversations yet",
                        size=18,
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
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
    else:
        content = ft.ListView(
            controls=tiles,
            expand=True,
            spacing=4,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

    appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            tooltip="Back",
            on_click=lambda e: on_back(),
        ),
        title=ft.Text(
            "History",
            weight=ft.FontWeight.W_600,
            size=20,
        ),
        center_title=True,
        bgcolor=ft.Colors.SURFACE,
    )

    view = ft.View(
        route="/history",
        controls=[content],
        appbar=appbar,
        bgcolor=ft.Colors.SURFACE,
        padding=0,
    )

    return view
