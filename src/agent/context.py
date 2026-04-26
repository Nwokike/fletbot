"""Context builder — constructs system prompts for the consumer assistant.

Centralises all system-prompt logic so the runner stays thin.
Integrates the memory system for cross-session recall.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent.memory import MemoryStore


# The consumer-facing system prompt template.
_SYSTEM_TEMPLATE = """\
You are FletBot, a friendly and helpful AI assistant powered by \
Google's Gemma 4 model.

Key traits:
- You are concise but thorough
- You format responses with markdown when appropriate \
(bold, lists, code blocks, etc.)
- You are honest about your limitations
- You maintain a warm, approachable tone
- You remember context within the current conversation
- You use your long-term memory to personalize responses

Current date and time: {current_time}
{extra_context}\
"""


class ContextBuilder:
    """Builds the system prompt injected into every LLM call."""

    def __init__(
        self,
        *,
        user_name: str | None = None,
        memory_store: MemoryStore | None = None,
    ):
        self._user_name = user_name
        self._memory = memory_store

    def build(self) -> str:
        """Return the fully-resolved system prompt."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        extra = ""
        if self._user_name:
            extra += f"The user's name is {self._user_name}.\n"
        if self._memory:
            mem_ctx = self._memory.get_memory_context()
            if mem_ctx:
                extra += f"\n{mem_ctx}\n"
            hist_ctx = self._memory.get_recent_history_context()
            if hist_ctx:
                extra += f"\n{hist_ctx}\n"
        return _SYSTEM_TEMPLATE.format(current_time=now, extra_context=extra)
