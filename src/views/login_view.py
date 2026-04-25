"""Login view — API key entry screen."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable

import flet as ft

logger = logging.getLogger(__name__)


def build_login_view(
    page: ft.Page,
    on_login_success: Callable[[], None],
    token_manager,
) -> ft.View:
    """Build the login/API key entry view."""

    api_key_field = ft.TextField(
        label="Google AI Studio API Key",
        hint_text="Paste your API key here",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        filled=True,
        prefix_icon=ft.Icons.KEY_ROUNDED,
        text_size=15,
    )

    status_text = ft.Text(
        "",
        size=13,
        color=ft.Colors.ERROR,
        visible=False,
    )

    loading_ring = ft.ProgressRing(
        width=20,
        height=20,
        stroke_width=2,
        visible=False,
    )

    async def validate_and_save(e):
        """Validate the API key and save if valid."""
        key = api_key_field.value
        if not key or not key.strip():
            status_text.value = "Please enter your API key"
            status_text.color = ft.Colors.ERROR
            status_text.visible = True
            page.update()
            return

        key = key.strip()

        # Show loading
        loading_ring.visible = True
        status_text.value = "Validating your API key..."
        status_text.color = ft.Colors.ON_SURFACE_VARIANT
        status_text.visible = True
        page.update()

        try:
            # Quick validation — try a minimal API call
            from src.providers.gemma_provider import ResilientGemmaProvider

            provider = ResilientGemmaProvider(api_key=key)
            is_valid = await provider.validate_api_key()
            await provider.close()

            if is_valid:
                await token_manager.save_api_key(key)
                loading_ring.visible = False
                status_text.value = "✓ API key verified!"
                status_text.color = ft.Colors.PRIMARY
                page.update()
                await asyncio.sleep(0.5)
                on_login_success()
            else:
                loading_ring.visible = False
                status_text.value = "Invalid API key. Please check and try again."
                status_text.color = ft.Colors.ERROR
                page.update()

        except Exception as exc:
            logger.error("API key validation error: %s", exc)
            loading_ring.visible = False
            status_text.value = f"Connection error: {str(exc)[:80]}"
            status_text.color = ft.Colors.ERROR
            page.update()

    def open_ai_studio(e):
        """Open Google AI Studio API key page."""
        page.launch_url("https://aistudio.google.com/apikey")

    # Build the view layout
    logo_icon = ft.Image(
        src="icon.png",
        width=80,
        height=80,
        fit=ft.BoxFit.CONTAIN,
    )

    title = ft.Text(
        "FletBot",
        size=32,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )

    subtitle = ft.Text(
        "Your AI assistant, powered by Gemma 4",
        size=15,
        color=ft.Colors.ON_SURFACE_VARIANT,
        text_align=ft.TextAlign.CENTER,
    )

    get_key_button = ft.TextButton(
        content="Get a free API key →",
        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
        on_click=open_ai_studio,
        style=ft.ButtonStyle(
            color=ft.Colors.PRIMARY,
        ),
    )

    continue_button = ft.FilledButton(
        content="Continue",
        icon=ft.Icons.ARROW_FORWARD_ROUNDED,
        on_click=validate_and_save,
        width=200,
        height=48,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    card_content = ft.Container(
        content=ft.Column(
            controls=[
                logo_icon,
                title,
                subtitle,
                ft.Container(height=20),
                api_key_field,
                ft.Container(height=4),
                get_key_button,
                ft.Container(height=8),
                ft.Row(
                    controls=[loading_ring, status_text],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=12),
                ft.Row(
                    controls=[continue_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        width=420,
        padding=40,
        border_radius=24,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 10),
        ),
    )

    # Wrap in a gradient container
    gradient_bg = ft.Container(
        content=ft.Container(
            content=card_content,
            alignment=ft.Alignment.CENTER,
            expand=True,
        ),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[
                "#0B1914",  # Very dark green
                "#050A08",  # Almost black
                "#1A1400",  # Very dark gold/brown
            ],
        ),
    )

    view = ft.View(
        route="/login",
        controls=[gradient_bg],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=0,
    )

    return view
