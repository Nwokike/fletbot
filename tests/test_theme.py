import pytest
import flet as ft
from src.theme import tokens, colors

def test_tokens():
    assert tokens.SPACE_MD > 0
    assert tokens.RADIUS_MD > 0
    assert tokens.FONT_LG == 18

def test_colors():
    assert colors.KIRI_GREEN.startswith("#")
    assert colors.BG_DARK_1.startswith("#")

def test_brand_gradient():
    grad = colors.brand_gradient(ft.ThemeMode.DARK)
    assert isinstance(grad, ft.LinearGradient)
    # The actual count is 3 (BG_DARK_1, BG_DARK_2, BG_DARK_3)
    assert len(grad.colors) == 3

def test_user_bubble_gradient():
    grad = colors.user_bubble_gradient()
    assert isinstance(grad, ft.LinearGradient)
    assert len(grad.colors) == 2
