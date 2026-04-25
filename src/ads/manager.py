"""Ad manager — AdMob integration via flet-ads.

Uses test ad unit IDs during development.
Only active on iOS/Android (no ads on desktop).

AdMob test values (from official Flet docs):
- App ID: ca-app-pub-3940256099942544~3347511713
- Banner (Android): ca-app-pub-3940256099942544/9214589741
- Banner (iOS): ca-app-pub-3940256099942544/2435281174
- Interstitial (Android): ca-app-pub-3940256099942544/1033173712
- Interstitial (iOS): ca-app-pub-3940256099942544/4411468910
"""

from __future__ import annotations

import logging

import flet as ft

logger = logging.getLogger(__name__)

# Test ad unit IDs (replace with production IDs before release)
_TEST_BANNER_ANDROID = "ca-app-pub-3940256099942544/9214589741"
_TEST_BANNER_IOS = "ca-app-pub-3940256099942544/2435281174"
_TEST_INTERSTITIAL_ANDROID = "ca-app-pub-3940256099942544/1033173712"
_TEST_INTERSTITIAL_IOS = "ca-app-pub-3940256099942544/4411468910"


class AdManager:
    """Manages ad display for FletBot.

    Only shows ads on mobile platforms (Android/iOS).
    Uses test IDs during development.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self._is_mobile = page.platform in (
            ft.PagePlatform.ANDROID,
            ft.PagePlatform.IOS,
        )

    def create_banner_ad(self) -> ft.Control | None:
        """Create a banner ad control, or None if not on mobile."""
        if not self._is_mobile:
            logger.info("Skipping ads — not on mobile platform")
            return None

        try:
            from flet_ads import BannerAd

            unit_id = (
                _TEST_BANNER_ANDROID
                if self.page.platform == ft.PagePlatform.ANDROID
                else _TEST_BANNER_IOS
            )

            banner = BannerAd(
                unit_id=unit_id,
                on_load=lambda e: logger.info("Banner ad loaded"),
                on_error=lambda e: logger.warning("Banner ad error: %s", e.data),
            )
            return banner

        except ImportError:
            logger.warning("flet-ads not available — ads disabled")
            return None

    @property
    def is_mobile(self) -> bool:
        return self._is_mobile
