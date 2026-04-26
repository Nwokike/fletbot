import pytest
import flet as ft
from src.components.message_bubble import MessageBubble, ThinkingIndicator
from src.providers.base import MediaPart

def test_message_bubble_user():
    bubble = MessageBubble(role="user", content="Hello")
    assert bubble._role == "user"
    assert bubble._content == "Hello"
    assert bubble.gradient is not None
    assert bubble.bgcolor is None

def test_message_bubble_ai():
    bubble = MessageBubble(role="assistant", content="Hi")
    assert bubble._role == "assistant"
    assert bubble.gradient is None
    assert bubble.bgcolor is not None

def test_message_bubble_with_media():
    media = [MediaPart(mime_type="image/jpeg", data=b"fake-data")]
    bubble = MessageBubble(role="user", content="Look at this", media=media)
    # Check if image is in the controls
    # The bubble content is a Column, the image is inside another Container in that Column
    column = bubble.content
    assert len(column.controls) > 1 # role label + media column + text

def test_thinking_indicator():
    indicator = ThinkingIndicator()
    assert "thinking" in indicator.content.controls[1].value
