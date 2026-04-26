"""Design system — colour palette and gradient definitions.

Every colour used anywhere in FletBot lives here.  Import from
``theme.colors`` instead of hard-coding hex strings.
"""

from __future__ import annotations

import flet as ft

# ── Brand ───────────────────────────────────────────────────────────
KIRI_GREEN = "#00A859"
KIRI_GREEN_DARK = "#008A49"
KIRI_GREEN_DEEP = "#006B38"
KIRI_GOLD = "#FFD700"
KIRI_GOLD_DIM = "#C9A800"

# ── Background gradient stops (dark mode) ───────────────────────────
BG_DARK_1 = "#0B1914"  # Deep forest
BG_DARK_2 = "#050A08"  # Near-black
BG_DARK_3 = "#1A1400"  # Dark gold tint

# ── Glassmorphism ───────────────────────────────────────────────────
GLASS_BG_OPACITY = 0.05
GLASS_BORDER_OPACITY = 0.10
GLASS_BG = ft.Colors.with_opacity(GLASS_BG_OPACITY, ft.Colors.WHITE)
GLASS_BORDER_COLOR = ft.Colors.with_opacity(GLASS_BORDER_OPACITY, ft.Colors.WHITE)

# ── Shadows ─────────────────────────────────────────────────────────
SHADOW_PRIMARY = ft.Colors.with_opacity(0.20, KIRI_GREEN)
SHADOW_DARK = ft.Colors.with_opacity(0.10, ft.Colors.BLACK)

# ── User bubble gradient ────────────────────────────────────────────
USER_BUBBLE_COLORS = [KIRI_GREEN, KIRI_GREEN_DARK]

# ── Reusable gradient objects ───────────────────────────────────────
def brand_gradient() -> ft.LinearGradient:
    """The standard dark background gradient used on all views."""
    return ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=[BG_DARK_1, BG_DARK_2, BG_DARK_3],
    )


def user_bubble_gradient() -> ft.LinearGradient:
    """Gradient for user chat bubbles."""
    return ft.LinearGradient(
        begin=ft.Alignment.BOTTOM_LEFT,
        end=ft.Alignment.TOP_RIGHT,
        colors=USER_BUBBLE_COLORS,
    )
