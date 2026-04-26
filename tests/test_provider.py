import pytest
from unittest.mock import MagicMock, patch
from src.providers.gemma_provider import ResilientGemmaProvider
from src.providers.base import ChatMessage

def test_gemma_provider_init():
    api_key = "test_key"
    provider = ResilientGemmaProvider(api_key=api_key)
    assert provider.api_key == api_key
    assert "gemma-4-31b-it" in provider.models

def test_build_request_body():
    provider = ResilientGemmaProvider(api_key="key")
    messages = [ChatMessage(role="user", content="Hello")]
    body = provider._build_request_body(messages)
    
    assert "contents" in body
    assert body["contents"][0]["role"] == "user"
    assert body["contents"][0]["parts"][0]["text"] == "Hello"

@pytest.mark.asyncio
async def test_generate_success():
    provider = ResilientGemmaProvider(api_key="key")
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Hi there!"}]},
                    "finishReason": "STOP"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        messages = [ChatMessage(role="user", content="Hi")]
        result = await provider.generate(messages)
        
        assert result.content == "Hi there!"
        assert result.model_used == "Gemma 4"

def test_parse_response_error():
    provider = ResilientGemmaProvider(api_key="key")
    data = {"candidates": []}
    result = provider._parse_response(data, "test-model")
    assert result.finish_reason == "ERROR"
