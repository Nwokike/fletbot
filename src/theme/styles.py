"""Design system — reusable widget factories and style presets.

Use these instead of building raw containers with hardcoded values.
"""

from __future__ import annotations

import flet as ft

from src.theme import colors, tokens


# ── Glass Card ──────────────────────────────────────────────────────
def glass_card(
    content: ft.Control,
    *,
    width: int | None = tokens.CARD_MAX_WIDTH,
    padding: int | ft.Padding = tokens.SPACE_XXXL,
    border_radius: int = tokens.RADIUS_XXL,
    blur_sigma: int = tokens.BLUR_SM,
) -> ft.Container:
    """Return a frosted-glass card container."""
    return ft.Container(
        content=content,
        width=width,
        padding=padding,
        border_radius=border_radius,
        bgcolor=colors.GLASS_BG,
        blur=ft.Blur(blur_sigma, blur_sigma, ft.BlurTileMode.MIRROR),
        border=ft.Border.all(1, colors.GLASS_BORDER_COLOR),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=tokens.SHADOW_BLUR_LG,
            color=colors.SHADOW_DARK,
            offset=ft.Offset(0, tokens.SHADOW_OFFSET_Y_LG),
        ),
    )


# ── Gradient Background ─────────────────────────────────────────────
def brand_gradient_bg(content: ft.Control, page: ft.Page | None = None) -> ft.Container:
    """Wrap *content* in the standard brand gradient background."""
    theme_mode = page.theme_mode if page else ft.ThemeMode.DARK
    return ft.Container(
        content=content,
        expand=True,
        gradient=colors.brand_gradient(theme_mode),
    )


# ── Primary Bubble Shadow ───────────────────────────────────────────
def primary_shadow() -> ft.BoxShadow:
    """Shadow for user message bubbles (green glow)."""
    return ft.BoxShadow(
        spread_radius=0,
        blur_radius=tokens.SHADOW_BLUR,
        color=colors.SHADOW_PRIMARY,
        offset=ft.Offset(0, tokens.SHADOW_OFFSET_Y),
    )


def dark_shadow() -> ft.BoxShadow:
    """Shadow for AI message bubbles (subtle dark)."""
    return ft.BoxShadow(
        spread_radius=0,
        blur_radius=tokens.SHADOW_BLUR,
        color=colors.SHADOW_DARK,
        offset=ft.Offset(0, tokens.SHADOW_OFFSET_Y),
    )


# ── Button Styles ───────────────────────────────────────────────────
def chip_button_style() -> ft.ButtonStyle:
    """Consistent style for quick-action / suggestion chips."""
    return ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_XL),
        padding=ft.Padding.symmetric(
            horizontal=tokens.SPACE_LG, vertical=tokens.SPACE_SM
        ),
    )


def filled_primary_style() -> ft.ButtonStyle:
    """Standard filled primary button (Continue, Send, etc.)."""
    return ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD),
    )


def outlined_danger_style() -> ft.ButtonStyle:
    """Outlined destructive button (Sign Out, Delete, etc.)."""
    return ft.ButtonStyle(
        color=ft.Colors.ERROR,
        side=ft.BorderSide(1, ft.Colors.ERROR),
        shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD),
        padding=ft.Padding.symmetric(
            horizontal=tokens.SPACE_XXL, vertical=tokens.SPACE_MD
        ),
    )


# ── Section Header (Settings) ──────────────────────────────────────
def section_header(title: str) -> ft.Container:
    """Reusable section header for Settings-style lists."""
    return ft.Container(
        content=ft.Text(
            title,
            size=tokens.FONT_SM,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.PRIMARY,
        ),
        padding=ft.Padding.only(
            left=tokens.SPACE_LG, top=tokens.SPACE_XL, bottom=tokens.SPACE_XS
        ),
    )


# ── Setting Tile ────────────────────────────────────────────────────
def setting_tile(
    icon: str,
    title: str,
    subtitle: str = "",
    trailing: ft.Control | None = None,
    on_click=None,
) -> ft.Container:
    """Reusable row for Settings lists."""
    children: list[ft.Control] = [
        ft.Icon(icon, size=tokens.ICON_LG, color=ft.Colors.ON_SURFACE_VARIANT),
        ft.Column(
            controls=[
                ft.Text(title, size=tokens.FONT_MD, weight=ft.FontWeight.W_500),
                *(
                    [
                        ft.Text(
                            subtitle,
                            size=tokens.FONT_XS,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        )
                    ]
                    if subtitle
                    else []
                ),
            ],
            spacing=tokens.SPACE_XXS,
            expand=True,
        ),
    ]
    if trailing:
        children.append(trailing)

    return ft.Container(
        content=ft.Row(
            controls=children,
            spacing=tokens.SPACE_LG,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(
            horizontal=tokens.SPACE_LG, vertical=14
        ),
        border_radius=tokens.RADIUS_MD,
        ink=True,
        on_click=on_click,
    )


# ── AppBar Builder ──────────────────────────────────────────────────
def standard_appbar(
    title: str,
    *,
    leading: ft.Control | None = None,
    actions: list[ft.Control] | None = None,
    transparent: bool = False,
) -> ft.AppBar:
    """Build a consistent AppBar across all views."""
    return ft.AppBar(
        leading=leading,
        title=ft.Text(
            title,
            weight=ft.FontWeight.W_600,
            size=tokens.FONT_XL,
        ),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT if transparent else ft.Colors.SURFACE,
        actions=actions or [],
    )
