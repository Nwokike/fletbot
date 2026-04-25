"""Settings view — user preferences and account management."""

from __future__ import annotations

import logging

import flet as ft

logger = logging.getLogger(__name__)


def build_settings_view(
    page: ft.Page,
    token_manager,
    on_back: callable,
    on_logout: callable,
) -> ft.View:
    """Build the settings view."""

    def _section_header(title: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(
                title,
                size=13,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.PRIMARY,
            ),
            padding=ft.padding.only(left=16, top=20, bottom=4),
        )

    def _setting_tile(
        icon: str,
        title: str,
        subtitle: str = "",
        trailing: ft.Control = None,
        on_click=None,
    ) -> ft.Container:
        controls = [
            ft.Icon(icon, size=22, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Column(
                controls=[
                    ft.Text(title, size=15, weight=ft.FontWeight.W_500),
                    *(
                        [
                            ft.Text(
                                subtitle,
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            )
                        ]
                        if subtitle
                        else []
                    ),
                ],
                spacing=2,
                expand=True,
            ),
        ]
        if trailing:
            controls.append(trailing)

        return ft.Container(
            content=ft.Row(
                controls=controls,
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            border_radius=12,
            ink=True,
            on_click=on_click,
        )

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
        from session.manager import SessionManager

        sm = SessionManager()
        count = sm.clear_all()
        page.open(
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

    controls = [
        # AI Model section
        _section_header("AI MODEL"),
        _setting_tile(
            ft.Icons.AUTO_AWESOME_ROUNDED,
            "Primary Model",
            "Gemma 4 26B (MoE) — Fast & efficient",
        ),
        _setting_tile(
            ft.Icons.BACKUP_ROUNDED,
            "Fallback Model",
            "Gemma 4 31B (Dense) — Maximum quality",
        ),
        # Appearance section
        _section_header("APPEARANCE"),
        _setting_tile(
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
        _section_header("ACCOUNT"),
        _setting_tile(
            ft.Icons.KEY_ROUNDED,
            "API Key",
            "Change or remove your Google AI Studio key",
            trailing=ft.Icon(
                ft.Icons.CHEVRON_RIGHT_ROUNDED,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            on_click=change_api_key,
        ),
        # Data section
        _section_header("DATA"),
        _setting_tile(
            ft.Icons.DELETE_SWEEP_ROUNDED,
            "Clear All Conversations",
            "Permanently delete all chat history",
            on_click=clear_conversations,
        ),
        # About section
        _section_header("ABOUT"),
        _setting_tile(
            ft.Icons.INFO_OUTLINE_ROUNDED,
            "FletBot v0.1.0",
            "Consumer AI assistant powered by Gemma 4",
        ),
        _setting_tile(
            ft.Icons.CODE_ROUNDED,
            "GitHub",
            "github.com/Nwokike/fletbot",
            on_click=lambda e: page.launch_url("https://github.com/Nwokike/fletbot"),
        ),
        ft.Container(height=20),
        # Logout button
        ft.Container(
            content=ft.OutlinedButton(
                content="Sign Out",
                icon=ft.Icons.LOGOUT_ROUNDED,
                on_click=logout,
                style=ft.ButtonStyle(
                    color=ft.Colors.ERROR,
                    side=ft.BorderSide(1, ft.Colors.ERROR),
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=ft.padding.symmetric(horizontal=24, vertical=12),
                ),
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.padding.only(bottom=20),
        ),
    ]

    appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            tooltip="Back",
            on_click=lambda e: on_back(),
        ),
        title=ft.Text(
            "Settings",
            weight=ft.FontWeight.W_600,
            size=20,
        ),
        center_title=True,
        bgcolor=ft.Colors.SURFACE,
    )

    view = ft.View(
        route="/settings",
        controls=[
            ft.ListView(
                controls=controls,
                expand=True,
                padding=ft.padding.symmetric(horizontal=4),
            ),
        ],
        appbar=appbar,
        bgcolor=ft.Colors.SURFACE,
        padding=0,
    )

    return view
