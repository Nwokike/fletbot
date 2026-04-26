"""Agent runner — simplified agent loop for consumer chat.

Adapted from Nanobot's agent/runner.py but stripped down for consumer use:
- Streaming support
- Uses ContextBuilder for system prompts
- Multimodal message support (images, audio)
"""

from __future__ import annotations

import logging
import time
from typing import AsyncGenerator

from agent.context import ContextBuilder
from providers.base import ChatMessage, GenerationResult, MediaPart
from providers.gemma_provider import ResilientGemmaProvider
from session.manager import Session

logger = logging.getLogger(__name__)


class AgentRunner:
    """Simplified agent runner for consumer chat.

    Handles the message → LLM → response flow with streaming support.
    """

    def __init__(self, provider: ResilientGemmaProvider):
        self.provider = provider
        self._context = ContextBuilder()

    def _session_to_messages(self, session: Session) -> list[ChatMessage]:
        """Convert session history to provider message format."""
        messages = []
        for msg in session.messages:
            role = "model" if msg.role == "assistant" else "user"
            messages.append(ChatMessage(role=role, content=msg.content))
        return messages

    async def send_message(
        self,
        user_message: str,
        session: Session,
        media: list[MediaPart] | None = None,
    ) -> GenerationResult:
        """Send a message and get a complete response."""
        self.provider.system_instruction = self._context.build()
        messages = self._session_to_messages(session)
        messages.append(
            ChatMessage(role="user", content=user_message, media=media)
        )

        start = time.time()
        result = await self.provider.generate(messages)
        elapsed = time.time() - start

        logger.info(
            "Response from %s in %.1fs (%d tokens)",
            result.model_used,
            elapsed,
            result.usage.get("total_tokens", 0),
        )
        return result

    async def send_message_stream(
        self,
        user_message: str,
        session: Session,
        media: list[MediaPart] | None = None,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Send a message and stream the response.

        Yields (chunk, model_used) tuples as they arrive.
        """
        self.provider.system_instruction = self._context.build()
        messages = self._session_to_messages(session)
        messages.append(
            ChatMessage(role="user", content=user_message, media=media)
        )

        async for chunk, model in self.provider.generate_stream(messages):
            yield (chunk, model)
