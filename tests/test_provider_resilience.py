"""Tests for ResilientGemmaProvider — retry, fallback, and audio error handling.

Adapted from adkbot's provider test patterns.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.providers.base import ChatMessage, MediaPart
from src.providers.gemma_provider import (
    PRIMARY_MODEL,
    SECONDARY_MODEL,
    TERTIARY_MODEL,
    ResilientGemmaProvider,
    _AUDIO_MODALITY_ERROR,
)


@pytest.fixture
def provider():
    return ResilientGemmaProvider(api_key="test-key-123")


# ── Fallback behaviour ─────────────────────────────────────────────


class TestFallbackBehaviour:
    @pytest.mark.asyncio
    async def test_uses_primary_model_first(self, provider):
        """When primary succeeds, no fallback should occur."""
        mock_result = MagicMock()
        mock_result.content = "Hello!"
        mock_result.model_used = "Gemma 4"
        mock_result.usage = {"total_tokens": 10}

        provider._call_model = AsyncMock(return_value=mock_result)
        result = await provider.generate(
            [ChatMessage(role="user", content="Hi")]
        )
        assert result.content == "Hello!"
        # Should be called with the primary model
        provider._call_model.assert_called_once()
        call_args = provider._call_model.call_args
        assert call_args[0][0] == PRIMARY_MODEL

    @pytest.mark.asyncio
    async def test_falls_back_on_primary_failure(self, provider):
        """When primary fails, should try secondary."""
        mock_result = MagicMock()
        mock_result.content = "Fallback response"
        mock_result.model_used = "Gemma 4"
        mock_result.usage = {}

        provider._call_model = AsyncMock(
            side_effect=[
                RuntimeError("Primary failed"),
                mock_result,
            ]
        )
        result = await provider.generate(
            [ChatMessage(role="user", content="Hi")]
        )
        assert result.content == "Fallback response"
        assert provider._call_model.call_count == 2

    @pytest.mark.asyncio
    async def test_all_models_fail_raises(self, provider):
        """When all models fail, should raise the last error."""
        provider._call_model = AsyncMock(
            side_effect=RuntimeError("All dead")
        )
        with pytest.raises(RuntimeError, match="All dead"):
            await provider.generate(
                [ChatMessage(role="user", content="Hi")]
            )
        assert provider._call_model.call_count == len(provider.models)


# ── Audio modality error handling ──────────────────────────────────


class TestAudioModalityError:
    def test_strip_audio_media_removes_audio_parts(self, provider):
        """Audio media parts should be removed, non-audio kept."""
        messages = [
            ChatMessage(
                role="user",
                content="Listen to this",
                media=[
                    MediaPart(
                        mime_type="audio/wav",
                        data=b"audio-data",
                        filename="voice.wav",
                    ),
                    MediaPart(
                        mime_type="image/png",
                        data=b"image-data",
                        filename="photo.png",
                    ),
                ],
            )
        ]
        stripped = provider._strip_audio_media(messages)
        assert len(stripped) == 1
        assert len(stripped[0].media) == 1
        assert stripped[0].media[0].mime_type == "image/png"

    def test_strip_audio_media_sets_none_when_all_audio(self, provider):
        """When all media is audio, media should become None."""
        messages = [
            ChatMessage(
                role="user",
                content="",
                media=[
                    MediaPart(
                        mime_type="audio/mp3",
                        data=b"audio-data",
                        filename="song.mp3",
                    ),
                ],
            )
        ]
        stripped = provider._strip_audio_media(messages)
        assert stripped[0].media is None
        assert "cannot process audio" in stripped[0].content

    def test_strip_audio_media_preserves_non_media_messages(self, provider):
        """Messages without media should pass through unchanged."""
        messages = [
            ChatMessage(role="user", content="Just text"),
            ChatMessage(role="model", content="A reply"),
        ]
        stripped = provider._strip_audio_media(messages)
        assert len(stripped) == 2
        assert stripped[0].content == "Just text"
        assert stripped[1].content == "A reply"

    @pytest.mark.asyncio
    async def test_generate_retries_without_audio_on_modality_error(
        self, provider
    ):
        """On audio modality error, should strip audio and retry."""
        mock_result = MagicMock()
        mock_result.content = "Text-only response"
        mock_result.model_used = "Gemma 4"
        mock_result.usage = {}

        # First call fails with audio error, second succeeds
        provider._call_model = AsyncMock(
            side_effect=[
                RuntimeError(
                    f"API error 400: {_AUDIO_MODALITY_ERROR} for this model"
                ),
                mock_result,
            ]
        )
        messages = [
            ChatMessage(
                role="user",
                content="Transcribe this",
                media=[
                    MediaPart(
                        mime_type="audio/wav",
                        data=b"data",
                        filename="voice.wav",
                    )
                ],
            )
        ]
        result = await provider.generate(messages)
        assert result.content == "Text-only response"
        assert provider._call_model.call_count == 2


# ── Request body building ─────────────────────────────────────────


class TestRequestBodyBuilding:
    def test_build_request_body_basic(self, provider):
        """Basic message should produce correct API body."""
        body = provider._build_request_body(
            [ChatMessage(role="user", content="Hello")]
        )
        assert "contents" in body
        assert len(body["contents"]) == 1
        assert body["contents"][0]["role"] == "user"
        assert body["contents"][0]["parts"][0]["text"] == "Hello"

    def test_build_request_body_with_system_instruction(self, provider):
        """System instruction should be included when set."""
        provider.system_instruction = "You are a helpful assistant"
        body = provider._build_request_body(
            [ChatMessage(role="user", content="Hi")]
        )
        assert "systemInstruction" in body
        assert (
            body["systemInstruction"]["parts"][0]["text"]
            == "You are a helpful assistant"
        )

    def test_build_request_body_with_media(self, provider):
        """Media parts should be base64-encoded in the body."""
        body = provider._build_request_body(
            [
                ChatMessage(
                    role="user",
                    content="What is this?",
                    media=[
                        MediaPart(
                            mime_type="image/png",
                            data=b"\x89PNG",
                            filename="test.png",
                        )
                    ],
                )
            ]
        )
        parts = body["contents"][0]["parts"]
        assert len(parts) == 2
        assert "inline_data" in parts[1]
        assert parts[1]["inline_data"]["mime_type"] == "image/png"

    def test_build_request_body_maps_assistant_to_model(self, provider):
        """'assistant' role should be mapped to 'model' for Gemini API."""
        body = provider._build_request_body(
            [ChatMessage(role="assistant", content="I'm here to help")]
        )
        assert body["contents"][0]["role"] == "model"

    def test_generation_config_in_body(self, provider):
        """Generation config should be present in request body."""
        body = provider._build_request_body(
            [ChatMessage(role="user", content="Hi")]
        )
        gen_config = body["generationConfig"]
        assert "temperature" in gen_config
        assert "topP" in gen_config
        assert "topK" in gen_config
        assert "maxOutputTokens" in gen_config


# ── Response parsing ───────────────────────────────────────────────


class TestResponseParsing:
    def test_parse_response_extracts_text(self, provider):
        """Should extract text from candidates."""
        data = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Hello there!"}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 5,
                "candidatesTokenCount": 3,
                "totalTokenCount": 8,
            },
        }
        result = provider._parse_response(data, "Gemma 4")
        assert result.content == "Hello there!"
        assert result.finish_reason == "STOP"
        assert result.usage["total_tokens"] == 8

    def test_parse_response_handles_empty_candidates(self, provider):
        """Empty candidates should return error result."""
        data = {"candidates": []}
        result = provider._parse_response(data, "Gemma 4")
        assert result.finish_reason == "ERROR"
        assert "couldn't generate" in result.content

    def test_parse_response_concatenates_multiple_parts(self, provider):
        """Multiple text parts should be concatenated."""
        data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Hello "},
                            {"text": "World!"},
                        ]
                    },
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {},
        }
        result = provider._parse_response(data, "Gemma 4")
        assert result.content == "Hello World!"
