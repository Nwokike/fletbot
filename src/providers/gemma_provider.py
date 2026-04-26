"""Resilient Gemma 4 provider with automatic fallback.

Uses DeepMind's Gemma 4 models via Google Generative Language API.

Extends ``LLMProvider`` from ``providers.base``.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import AsyncGenerator, Optional

import httpx

from src.providers.base import (
    ChatMessage,
    GenerationConfig,
    GenerationResult,
    LLMProvider,
    MediaPart,
)

logger = logging.getLogger(__name__)

# Gemini API base
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Default models
PRIMARY_MODEL = "gemma-4-31b-it"
SECONDARY_MODEL = "gemma-4-26b-a4b-it"
TERTIARY_MODEL = "gemini-3.1-flash-lite-preview"

# Retry config
_MAX_RETRIES = 5
_INITIAL_DELAY = 2.0
_MAX_DELAY = 60.0
_RETRY_STATUS_CODES = {429, 503, 500}

# Error messages that indicate the model doesn't support a specific modality
_AUDIO_MODALITY_ERROR = "audio input modality is not enabled"


# Re-export for convenience
ProviderResponse = GenerationResult


class ResilientGemmaProvider(LLMProvider):
    """Resilient provider with auto-fallback between Gemma 4 models.

    On any error from the primary model (rate limit, server error, etc.),
    automatically retries with exponential backoff, then falls back to
    the next model in the chain.
    """

    def __init__(
        self,
        api_key: str,
        models: list[str] = [PRIMARY_MODEL, SECONDARY_MODEL, TERTIARY_MODEL],
        generation_config: Optional[GenerationConfig] = None,
        system_instruction: Optional[str] = None,
    ):
        self.api_key = api_key
        self.models = models
        self.config = generation_config or GenerationConfig()
        self.system_instruction = system_instruction
        self._client = httpx.AsyncClient(timeout=120.0)

    # ── Request building ────────────────────────────────────────────
    def _build_request_body(
        self, messages: list[ChatMessage], tools: list[dict] | None = None
    ) -> dict:
        """Construct the Gemini API request body."""
        contents = []
        for msg in messages:
            role = "model" if msg.role == "assistant" else msg.role
            parts = []

            # Handle tool results (function responses)
            if msg.role == "tool" and msg.tool_result:
                parts.append(
                    {
                        "function_response": {
                            "name": msg.tool_result.name,
                            "response": {"content": msg.tool_result.content},
                        }
                    }
                )
            # Handle tool calls (function calls)
            elif msg.tool_calls:
                for tc in msg.tool_calls:
                    parts.append(
                        {
                            "function_call": {
                                "name": tc.name,
                                "args": tc.arguments,
                            }
                        }
                    )
            # Handle regular text/media
            else:
                if msg.content:
                    parts.append({"text": msg.content})

                if msg.media:
                    for media in msg.media:
                        parts.append(
                            {
                                "inline_data": {
                                    "mime_type": media.mime_type,
                                    "data": base64.b64encode(media.data).decode("utf-8"),
                                }
                            }
                        )
            if parts:
                contents.append({"role": role, "parts": parts})

        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.config.temperature,
                "topP": self.config.top_p,
                "topK": self.config.top_k,
                "maxOutputTokens": self.config.max_output_tokens,
            },
        }

        if self.system_instruction:
            body["systemInstruction"] = {"parts": [{"text": self.system_instruction}]}

        if tools:
            body["tools"] = tools

        return body

    # ── Public API (LLMProvider) ────────────────────────────────────
    async def generate(
        self, messages: list[ChatMessage], tools: list[dict] | None = None
    ) -> GenerationResult:
        """Generate a complete response with automated fallback/retry."""
        last_error = None

        for model in self.models:
            try:
                return await self._call_model(model, messages, tools=tools)
            except Exception as e:
                err_msg = str(e).lower()
                if _AUDIO_MODALITY_ERROR in err_msg:
                    # Strip audio and retry with the SAME model
                    stripped_messages = self._strip_audio_media(messages)
                    try:
                        return await self._call_model(model, stripped_messages, tools=tools)
                    except Exception as retry_e:
                        last_error = retry_e
                        continue
                last_error = e
                continue

        raise last_error or RuntimeError("All models failed")

    async def generate_stream(
        self, messages: list[ChatMessage]
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Stream a response, yielding (chunk, model_used) tuples."""
        last_error = None

        for model_name in self.models:
            try:
                async for chunk in self._stream_model(model_name, messages):
                    yield (chunk, "Gemma 4")
                return
            except Exception as e:
                error_str = str(e).lower()
                # If audio modality not supported, strip audio and retry same model
                if _AUDIO_MODALITY_ERROR in error_str:
                    logger.warning(
                        "Stream: model %s doesn't support audio — retrying without audio",
                        model_name,
                    )
                    stripped = self._strip_audio_media(messages)
                    try:
                        async for chunk in self._stream_model(model_name, stripped):
                            yield (chunk, "Gemma 4")
                        return
                    except Exception as e2:
                        last_error = e2
                        continue

                logger.error("Streaming from %s failed: %s", model_name, e)
                last_error = e
                if model_name != self.models[-1]:
                    logger.info("🔄 Falling back to next model for streaming...")
                continue

        if last_error:
            raise last_error

    async def validate_api_key(self) -> bool:
        """Test the API key with a minimal request."""
        try:
            result = await self._call_model(
                self.models[0],
                [ChatMessage(role="user", content="Hi")],
            )
            return bool(result.content)
        except Exception as e:
            logger.error("API key validation failed: %s", e)
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    # ── Internal ────────────────────────────────────────────────────
    async def _call_model(
        self, model: str, messages: list[ChatMessage], tools: list[dict] | None = None
    ) -> GenerationResult:
        """Call a single model with retry logic."""
        url = f"{_API_BASE}/models/{model}:generateContent"
        body = self._build_request_body(messages, tools=tools)
        delay = _INITIAL_DELAY

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await self._client.post(
                    url,
                    params={"key": self.api_key},
                    json=body,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_response(data, model)

                if response.status_code in _RETRY_STATUS_CODES:
                    logger.warning(
                        "Model %s returned %d (attempt %d/%d), retrying in %.1fs...",
                        model,
                        response.status_code,
                        attempt,
                        _MAX_RETRIES,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, _MAX_DELAY)
                    continue

                error_text = response.text[:500]
                raise RuntimeError(
                    f"API error {response.status_code} from {model}: {error_text}"
                )

            except httpx.TimeoutException:
                logger.warning(
                    "Timeout calling %s (attempt %d/%d)", model, attempt, _MAX_RETRIES
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, _MAX_DELAY)
                    continue
                raise

        raise RuntimeError(f"Max retries ({_MAX_RETRIES}) exceeded for model {model}")

    async def _stream_model(
        self, model: str, messages: list[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        """Stream from a single model with retry on initial connection."""
        url = f"{_API_BASE}/models/{model}:streamGenerateContent"
        body = self._build_request_body(messages)
        delay = _INITIAL_DELAY

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with self._client.stream(
                    "POST",
                    url,
                    params={"key": self.api_key, "alt": "sse"},
                    json=body,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status_code in _RETRY_STATUS_CODES:
                        logger.warning(
                            "Stream %s returned %d (attempt %d/%d)",
                            model,
                            response.status_code,
                            attempt,
                            _MAX_RETRIES,
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, _MAX_DELAY)
                        continue

                    if response.status_code != 200:
                        text = ""
                        async for chunk in response.aiter_text():
                            text += chunk
                            if len(text) > 500:
                                break
                        raise RuntimeError(
                            f"Stream error {response.status_code}: {text[:500]}"
                        )

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if not data_str:
                            continue
                        try:
                            data = json.loads(data_str)
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = (
                                    candidates[0].get("content", {}).get("parts", [])
                                )
                                for part in parts:
                                    text = part.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
                    return  # Successful stream

            except httpx.TimeoutException:
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, _MAX_DELAY)
                    continue
                raise

        raise RuntimeError(f"Max retries exceeded for streaming model {model}")

    @staticmethod
    def _strip_audio_media(messages: list[ChatMessage]) -> list[ChatMessage]:
        """Return a copy of messages with audio media parts removed."""
        _AUDIO_MIMES = {"audio/", "application/ogg"}
        stripped = []
        for msg in messages:
            if not msg.media:
                stripped.append(msg)
                continue
            non_audio = [
                m
                for m in msg.media
                if not any(m.mime_type.startswith(prefix) for prefix in _AUDIO_MIMES)
            ]
            stripped.append(
                ChatMessage(
                    role=msg.role,
                    content=msg.content or "(Audio was attached but this model cannot process audio)",
                    media=non_audio if non_audio else None,
                )
            )
        return stripped

    @staticmethod
    def _parse_response(data: dict, model: str) -> GenerationResult:
        """Parse the Gemini API response."""
        candidates = data.get("candidates", [])
        if not candidates:
            return GenerationResult(
                content="Error: Model couldn't generate a response (empty candidates).",
                model_used=model,
                finish_reason="ERROR",
            )

        candidate = candidates[0]
        content_obj = candidate.get("content", {})
        parts = content_obj.get("parts", [])

        # Extract text
        text_parts = [p.get("text") for p in parts if "text" in p]
        full_content = "".join(text_parts) if text_parts else ""

        # Extract tool calls
        tool_calls = []
        for p in parts:
            if "function_call" in p:
                fc = p["function_call"]
                # We use the name as ID if no explicit ID is provided
                tool_calls.append(
                    ToolCall(
                        call_id=fc.get("name"),
                        name=fc.get("name"),
                        arguments=fc.get("args", {}),
                    )
                )

        usage_meta = data.get("usageMetadata", {})
        usage = {
            "prompt_tokens": usage_meta.get("promptTokenCount", 0),
            "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
            "total_tokens": usage_meta.get("totalTokenCount", 0),
        }

        return GenerationResult(
            content=full_content,
            model_used=model,
            finish_reason=candidate.get("finishReason", "STOP"),
            usage=usage,
            tool_calls=tool_calls if tool_calls else None,
        )
