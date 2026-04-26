import pytest
import asyncio
import flet as ft
from unittest.mock import MagicMock, AsyncMock
from src.views.login_view import build_login_view
from src.views.settings_view import build_settings_view
from src.views.history_view import build_history_view
from src.session.manager import SessionManager
from src.auth.token_manager import TokenManager

def test_login_view_init(mock_page):
    mock_tm = MagicMock(spec=TokenManager)
    view = build_login_view(mock_page, on_login_success=lambda: None, token_manager=mock_tm)
    assert isinstance(view, ft.View)
    assert view.route == "/login"

@pytest.mark.asyncio
async def test_settings_view_init(mock_page):
    mock_tm = MagicMock(spec=TokenManager)
    mock_tm.get_api_key = AsyncMock(return_value="test_key_12345")
    
    view = await build_settings_view(mock_page, token_manager=mock_tm, on_back=lambda: None, on_logout=lambda: None)
    assert isinstance(view, ft.View)
    assert view.route == "/settings"

def test_history_view_init(mock_page):
    mock_sm = MagicMock(spec=SessionManager)
    mock_sm.list_sessions.return_value = []
    
    view = build_history_view(mock_page, mock_sm, on_select_session=lambda s: None, on_back=lambda: None)
    assert isinstance(view, ft.View)
    assert view.route == "/history"
