import pytest
import flet as ft
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_page():
    page = MagicMock(spec=ft.Page)
    page.overlay = []
    page.client_storage = MagicMock()
    page.clipboard = MagicMock()
    page.clipboard.set = AsyncMock()
    page.session_id = "test-session"
    return page
