"""Settings view — user preferences and account management.

Uses design system for all visual styling via ``section_header``
and ``setting_tile`` from ``theme.styles``.
"""

from __future__ import annotations

import logging

import flet as ft

from src.theme import tokens
from src.theme.styles import (
    brand_gradient_bg,
    outlined_danger_style,
    section_header,
    setting_tile,
    standard_appbar,
)

from src.ads.manager import AdManager

logger = logging.getLogger(__name__)


async def build_settings_view(
    page: ft.Page,
    token_manager,
    on_back: callable,
    on_logout: callable,
) -> ft.View:
    """Build the settings view."""

    # Theme toggle
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
        else:
            page.theme_mode = ft.ThemeMode.DARK
        page.update()

    theme_icon = (
        ft.Icons.DARK_MODE_ROUNDED
        if page.theme_mode == ft.ThemeMode.LIGHT
        else ft.Icons.LIGHT_MODE_ROUNDED
    )
    current_theme = "Dark" if page.theme_mode == ft.ThemeMode.DARK else "Light"

    # Change API Key
    async def change_api_key(e):
        await token_manager.clear_api_key()
        on_logout()

    # Clear all conversations
    async def clear_conversations(e):
        from src.session.manager import SessionManager

        sm = SessionManager()
        count = sm.clear_all()
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(f"Cleared {count} conversations"),
                action="OK",
            )
        )
        page.update()

    # Logout
    async def logout(e):
        await token_manager.clear_api_key()
        on_logout()

    # Export conversations
    async def export_conversations(e):
        from src.session.manager import SessionManager
        import json
        import os

        sm = SessionManager()
        sessions = sm.list_sessions()
        data = [s.to_dict() for s in sessions]
        
        # In a real app, we'd use a file picker to save. 
        # For now, we'll save to a known location and show a snackbar.
        export_path = os.path.expanduser("~/fletbot_export.json")
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Exported to {export_path}"))
            )
        except Exception as e:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Export failed: {e}"))
            )
        page.update()

    # Masked API Key
    api_key = await token_manager.get_api_key() or ""
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "********"

    controls = [
        # Appearance section
        section_header("APPEARANCE"),
        setting_tile(
            theme_icon,
            "Theme",
            f"Currently: {current_theme}",
            trailing=ft.Switch(
                value=(page.theme_mode == ft.ThemeMode.DARK),
                on_change=lambda e: toggle_theme(e),
                active_color=ft.Colors.PRIMARY,
            ),
        ),
        # Account section
        section_header("ACCOUNT"),
        setting_tile(
            ft.Icons.KEY_ROUNDED,
            "API Key",
            f"Current: {masked_key}",
            trailing=ft.Icon(
                ft.Icons.CHEVRON_RIGHT_ROUNDED,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            on_click=change_api_key,
        ),
        # AI Model section
        section_header("AI MODEL"),
        setting_tile(
            ft.Icons.SMART_TOY_ROUNDED,
            "Primary: Gemma 4 31B",
            "Dense model — maximum quality",
        ),
        setting_tile(
            ft.Icons.BOLT_ROUNDED,
            "Fallback: Gemma 4 26B",
            "MoE model — faster inference (4B active params)",
        ),
        setting_tile(
            ft.Icons.SPEED_ROUNDED,
            "Emergency: Gemini Flash Lite",
            "Lightweight fallback when Gemma models are unavailable",
        ),
        setting_tile(
            ft.Icons.OPEN_IN_NEW_ROUNDED,
            "About Gemma 4",
            "deepmind.google/models/gemma/gemma-4",
            on_click=lambda e: page.launch_url(
                "https://deepmind.google/models/gemma/gemma-4/"
            ),
        ),
        # Data section
        section_header("DATA"),
        setting_tile(
            ft.Icons.FILE_DOWNLOAD_OUTLINED,
            "Export Conversations",
            "Download all chat history as JSON",
            on_click=export_conversations,
        ),
        setting_tile(
            ft.Icons.DELETE_SWEEP_ROUNDED,
            "Clear All Conversations",
            "Permanently delete all chat history",
            on_click=clear_conversations,
        ),
        # Ad Placement
        (
            ft.Container(
                content=AdManager(page).create_settings_banner() or ft.Container(),
                padding=tokens.SPACE_MD,
            )
        ),
        # About section
        section_header("ABOUT"),
        setting_tile(
            ft.Icons.INFO_OUTLINE_ROUNDED,
            "FletBot v0.1.0",
            "Consumer AI assistant powered by Gemma 4",
        ),
        setting_tile(
            ft.Icons.CODE_ROUNDED,
            "GitHub",
            "github.com/Nwokike/fletbot",
            on_click=lambda e: page.launch_url(
                "https://github.com/Nwokike/fletbot"
            ),
        ),
        ft.Container(height=tokens.SPACE_XL),
        # Logout button
        ft.Container(
            content=ft.OutlinedButton(
                content="Sign Out",
                icon=ft.Icons.LOGOUT_ROUNDED,
                on_click=logout,
                style=outlined_danger_style(),
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(bottom=tokens.SPACE_XL),
        ),
    ]

    appbar = standard_appbar(
        "Settings",
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            tooltip="Back",
            on_click=lambda e: on_back(),
        ),
        transparent=True,
    )

    gradient_bg = brand_gradient_bg(
        ft.ListView(
            controls=controls,
            expand=True,
            padding=ft.Padding.symmetric(horizontal=tokens.SPACE_XS),
        ),
        page=page,
    )

    view = ft.View(
        route="/settings",
        controls=[gradient_bg],
        appbar=appbar,
        padding=0,
    )

    return view
