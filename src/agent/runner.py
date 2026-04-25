"""Agent runner — simplified agent loop for consumer chat.

Adapted from Nanobot's agent/runner.py but stripped down for consumer use:
- No tool execution (Phase 2)
- No subagents
- Simple message → response flow with streaming
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import AsyncGenerator

from providers.gemma_provider import (
    ChatMessage,
    GenerationResult,
    ResilientGemmaProvider,
)
from session.manager import Session

logger = logging.getLogger(__name__)

# System prompt for consumer assistant
SYSTEM_PROMPT = """You are FletBot, a friendly and helpful AI assistant. You are powered by Google's Gemma 4 model.

Key traits:
- You are concise but thorough
- You format responses with markdown when appropriate (bold, lists, code blocks, etc.)
- You are honest about your limitations
- You maintain a warm, approachable tone
- You remember context within the current conversation

Current date and time: {current_time}
"""


class AgentRunner:
    """Simplified agent runner for consumer chat.

    Handles the message → LLM → response flow with streaming support.
    """

    def __init__(self, provider: ResilientGemmaProvider):
        self.provider = provider

    def _build_system_prompt(self) -> str:
        """Build the system prompt with current context."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return SYSTEM_PROMPT.format(current_time=now)

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
    ) -> GenerationResult:
        """Send a message and get a complete response."""
        # Update system instruction
        self.provider.system_instruction = self._build_system_prompt()

        # Build message history from session
        messages = self._session_to_messages(session)

        # Add the new user message
        messages.append(ChatMessage(role="user", content=user_message))

        # Call the provider
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
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Send a message and stream the response.

        Yields (chunk, model_used) tuples as they arrive.
        """
        # Update system instruction
        self.provider.system_instruction = self._build_system_prompt()

        # Build message history from session
        messages = self._session_to_messages(session)

        # Add the new user message
        messages.append(ChatMessage(role="user", content=user_message))

        # Stream from provider
        async for chunk, model in self.provider.generate_stream(messages):
            yield (chunk, model)
