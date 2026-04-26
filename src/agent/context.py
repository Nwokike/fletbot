"""Context builder — constructs system prompts for the consumer assistant.

Centralises all system-prompt logic so the runner stays thin.
"""

from __future__ import annotations

from datetime import datetime, timezone


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

Current date and time: {current_time}
{extra_context}\
"""


class ContextBuilder:
    """Builds the system prompt injected into every LLM call."""

    def __init__(self, *, user_name: str | None = None):
        self._user_name = user_name

    def build(self) -> str:
        """Return the fully-resolved system prompt."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        extra = ""
        if self._user_name:
            extra += f"The user's name is {self._user_name}.\n"
        return _SYSTEM_TEMPLATE.format(current_time=now, extra_context=extra)
