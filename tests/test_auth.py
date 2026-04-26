import pytest
from unittest.mock import patch, AsyncMock
from src.auth.token_manager import TokenManager

@pytest.fixture
def mock_token_manager(mock_page):
    with patch('src.auth.token_manager.ft.SharedPreferences') as mock_prefs_cls:
        mock_prefs = MagicMock()
        mock_prefs.get = AsyncMock()
        mock_prefs.set = AsyncMock()
        mock_prefs.remove = AsyncMock()
        mock_prefs_cls.return_value = mock_prefs
        
        tm = TokenManager(mock_page)
        tm._prefs = mock_prefs  # Injecting explicitly just in case
        return tm, mock_prefs

from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_token_manager_init(mock_page):
    with patch('src.auth.token_manager.ft.SharedPreferences'):
        tm = TokenManager(mock_page)
        assert tm is not None

@pytest.mark.asyncio
async def test_get_api_key_from_storage(mock_token_manager):
    tm, mock_prefs = mock_token_manager
    mock_prefs.get.return_value = "stored_key"
    
    key = await tm.get_api_key()
    assert key == "stored_key"
    mock_prefs.get.assert_called_with("fletbot_api_key")

@pytest.mark.asyncio
async def test_save_api_key(mock_token_manager):
    tm, mock_prefs = mock_token_manager
    await tm.save_api_key("new_key")
    mock_prefs.set.assert_called_with("fletbot_api_key", "new_key")

@pytest.mark.asyncio
async def test_clear_api_key(mock_token_manager):
    tm, mock_prefs = mock_token_manager
    await tm.clear_api_key()
    mock_prefs.remove.assert_called_with("fletbot_api_key")
