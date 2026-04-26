import pytest
from unittest.mock import MagicMock, patch
from src.ads.manager import AdManager

def test_ad_manager_init(mock_page):
    # On desktop/web, ads should be unavailable
    with patch('src.ads.manager._is_mobile', return_value=False):
        am = AdManager(mock_page)
        assert am.available is False

def test_ad_manager_mobile_available(mock_page):
    # Mock mobile platform and flet_ads present
    with patch('src.ads.manager._is_mobile', return_value=True), \
         patch('src.ads.manager._HAS_ADS', True):
        am = AdManager(mock_page)
        assert am.available is True

def test_create_banner_desktop(mock_page):
    am = AdManager(mock_page) # desktop by default in tests
    banner = am.create_inline_banner()
    assert banner is None

def test_create_banner_mobile(mock_page):
    with patch('src.ads.manager._is_mobile', return_value=True), \
         patch('src.ads.manager._HAS_ADS', True), \
         patch('src.ads.manager.BannerAd') as mock_banner:
        am = AdManager(mock_page)
        banner = am.create_inline_banner()
        assert banner is not None
        mock_banner.assert_called()
