"""Abstract LLM provider interface.

All AI providers (Gemma, future models) extend this base.
Shared data classes live here to avoid circular imports.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional


@dataclass
class ChatMessage:
    """A single chat message in provider-neutral format."""

    role: str  # "user" or "model"
    content: str
    media: list[MediaPart] | None = None


@dataclass
class MediaPart:
    """A media attachment (image, audio, document) for multimodal input."""

    mime_type: str  # e.g. "image/jpeg", "audio/wav"
    data: bytes  # Raw file bytes
    filename: str = ""


@dataclass
class GenerationConfig:
    """Configuration for text generation."""

    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192


@dataclass
class GenerationResult:
    """Result from a generation call."""

    content: str
    model_used: str
    finish_reason: str = "STOP"
    usage: dict = field(default_factory=dict)


class LLMProvider(abc.ABC):
    """Abstract base class for all LLM providers."""

    @abc.abstractmethod
    async def generate(self, messages: list[ChatMessage]) -> GenerationResult:
        """Generate a complete response."""

    @abc.abstractmethod
    async def generate_stream(
        self, messages: list[ChatMessage]
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Stream a response, yielding (chunk, model_used) tuples."""
        yield ("", "")  # pragma: no cover — needed for type checker

    @abc.abstractmethod
    async def validate_api_key(self) -> bool:
        """Test that the configured credentials are valid."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Release resources (HTTP clients, etc.)."""
