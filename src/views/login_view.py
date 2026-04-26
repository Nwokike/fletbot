"""Login view — API key entry screen.

Uses design system for all visual styling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable

import flet as ft

from theme import colors, tokens
from theme.styles import brand_gradient_bg, filled_primary_style, glass_card

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
        border_radius=tokens.RADIUS_MD,
        filled=True,
        prefix_icon=ft.Icons.KEY_ROUNDED,
        text_size=tokens.FONT_MD,
    )

    status_text = ft.Text(
        "",
        size=tokens.FONT_SM,
        color=ft.Colors.ERROR,
        visible=False,
    )

    loading_ring = ft.ProgressRing(
        width=tokens.ICON_MD,
        height=tokens.ICON_MD,
        stroke_width=tokens.PROGRESS_STROKE,
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
            from providers.gemma_provider import ResilientGemmaProvider

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
            page.show_dialog(
                ft.SnackBar(content=ft.Text(f"Error: {str(exc)[:100]}"))
            )

    def open_ai_studio(e):
        """Open Google AI Studio API key page."""
        page.launch_url("https://aistudio.google.com/apikey")

    # Build the view layout
    logo_icon = ft.Image(
        src="icon.png",
        width=tokens.ICON_LOGO_LG,
        height=tokens.ICON_LOGO_LG,
        fit=ft.BoxFit.CONTAIN,
    )

    title = ft.Text(
        "FletBot",
        size=tokens.FONT_TITLE,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )

    subtitle = ft.Text(
        "Your AI assistant, powered by Gemma 4",
        size=tokens.FONT_MD,
        color=ft.Colors.ON_SURFACE_VARIANT,
        text_align=ft.TextAlign.CENTER,
    )

    get_key_button = ft.TextButton(
        content="Get a free API key →",
        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
        on_click=open_ai_studio,
        style=ft.ButtonStyle(color=ft.Colors.PRIMARY),
    )

    continue_button = ft.FilledButton(
        content="Continue",
        icon=ft.Icons.ARROW_FORWARD_ROUNDED,
        on_click=validate_and_save,
        width=200,
        height=48,
        style=filled_primary_style(),
    )

    card_content_col = ft.Column(
        controls=[
            logo_icon,
            title,
            subtitle,
            ft.Container(height=tokens.SPACE_XL),
            api_key_field,
            ft.Container(height=tokens.SPACE_XS),
            get_key_button,
            ft.Container(height=tokens.SPACE_SM),
            ft.Row(
                controls=[loading_ring, status_text],
                spacing=tokens.SPACE_SM,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(height=tokens.SPACE_MD),
            ft.Row(
                controls=[continue_button],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=tokens.SPACE_XS,
    )

    card = glass_card(card_content_col)

    # Wrap in brand gradient
    gradient_bg = brand_gradient_bg(
        ft.Container(
            content=card,
            alignment=ft.Alignment.CENTER,
            expand=True,
        ),
        page=page,
    )

    view = ft.View(
        route="/login",
        controls=[gradient_bg],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=0,
    )

    return view
