"""AdMob manager — real Google test ad integration.

Uses official Google AdMob test IDs for development.
Provides inline banner ads for smart placement between messages,
in settings, and in history views.

Production: Replace APP_ID and unit IDs with real publisher values.
"""

from __future__ import annotations

import logging
import sys

import flet as ft

from src.theme import tokens

logger = logging.getLogger(__name__)

# ── Official Google AdMob Test Values ───────────────────────────────
# Source: https://flet.dev/docs/controls/ads/#test-values
TEST_APP_ID = "ca-app-pub-3940256099942544~3347511713"

# BannerAd test unit IDs (per platform)
TEST_BANNER_ANDROID = "ca-app-pub-3940256099942544/9214589741"
TEST_BANNER_IOS = "ca-app-pub-3940256099942544/2435281174"

# InterstitialAd test unit IDs (per platform)
TEST_INTERSTITIAL_ANDROID = "ca-app-pub-3940256099942544/1033173712"
TEST_INTERSTITIAL_IOS = "ca-app-pub-3940256099942544/4411468910"

# flet-ads is mobile only
_HAS_ADS = False
try:
    from flet_ads import BannerAd, InterstitialAd

    _HAS_ADS = True
except ImportError:
    pass


def _is_mobile() -> bool:
    """Check if running on a mobile platform."""
    return sys.platform not in ("win32", "linux", "darwin")


def _banner_unit_id() -> str:
    """Return the correct banner unit ID for the current platform."""
    if sys.platform == "darwin":
        return TEST_BANNER_IOS
    return TEST_BANNER_ANDROID


def _interstitial_unit_id() -> str:
    """Return the correct interstitial unit ID for the current platform."""
    if sys.platform == "darwin":
        return TEST_INTERSTITIAL_IOS
    return TEST_INTERSTITIAL_ANDROID


class AdManager:
    """Manages ad display throughout the app.

    Ad strategy: Smart inline banners placed between content,
    never interstitials (professional UX).
    """

    def __init__(self, page: ft.Page):
        self._page = page
        self._available = _HAS_ADS and _is_mobile()
        if self._available:
            logger.info("AdMob available — using test IDs for development")
        else:
            logger.info("AdMob not available (desktop/web) — ads disabled")

    @property
    def available(self) -> bool:
        return self._available

    def create_inline_banner(self) -> ft.Container | None:
        """Create a banner ad wrapped in a styled container.

        Returns None on desktop/web where ads aren't supported.
        This is designed to be inserted between chat messages,
        history tiles, or settings sections.
        """
        if not self._available:
            return None

        try:
            banner = BannerAd(
                unit_id=_banner_unit_id(),
                on_click=lambda e: logger.info("Ad clicked"),
                on_error=lambda e: logger.warning("Ad error: %s", e),
                on_impression=lambda e: logger.info("Ad impression"),
                on_open=lambda e: logger.info("Ad opened"),
                on_close=lambda e: logger.info("Ad closed"),
                on_will_dismiss=lambda e: logger.info("Ad will dismiss"),
            )

            return ft.Container(
                content=banner,
                padding=ft.Padding.symmetric(
                    horizontal=tokens.SPACE_MD, vertical=tokens.SPACE_SM
                ),
                border_radius=tokens.RADIUS_MD,
                margin=ft.Margin.symmetric(
                    horizontal=tokens.SPACE_SM, vertical=tokens.SPACE_XS
                ),
                alignment=ft.Alignment.CENTER,
            )
        except Exception as e:
            logger.warning("Failed to create banner ad: %s", e)
            return None

    def create_settings_banner(self) -> ft.Container | None:
        """Create a smaller banner for settings/history views."""
        return self.create_inline_banner()
