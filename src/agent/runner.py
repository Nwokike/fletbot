"""Agent runner — simplified agent loop for consumer chat.

Adapted from adkbot's agent/runner.py but stripped down for consumer use:
- Streaming support
- Uses ContextBuilder for system prompts
- Multimodal message support (images, audio)
- Memory integration for cross-session recall
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncGenerator, Optional

from src.agent.context import ContextBuilder
from src.agent.memory import MemoryStore
from src.agent.tools import TOOLS_METADATA, execute_tool
from src.providers.base import ChatMessage, LLMProvider, MediaPart, ToolCall, ToolResult
from src.providers.gemma_provider import ResilientGemmaProvider
from src.session.manager import Session

logger = logging.getLogger(__name__)


class AgentRunner:
    """Simplified agent runner for consumer chat.

    Handles the message → LLM → response flow with streaming support
    and persistent memory.
    """

    def __init__(
        self,
        provider: ResilientGemmaProvider,
        memory_store: Optional[MemoryStore] = None,
    ):
        self.provider = provider
        self._memory = memory_store or MemoryStore()

    @property
    def memory(self) -> MemoryStore:
        """Expose the memory store for external access."""
        return self._memory

    async def send_message(
        self,
        text: str,
        session: Session,
        media: list[MediaPart] | None = None,
        user_name: str | None = None,
    ) -> str:
        """Send a message to the AI and get a full response (with tool loop)."""
        messages = self._build_messages(text, session, media, user_name)

        # Tool execution loop
        max_iterations = 5
        for _ in range(max_iterations):
            result = await self.provider.generate(messages, tools=TOOLS_METADATA)

            # If no tool calls, return final content
            if not result.tool_calls:
                # Add model response to session
                session.add_message("assistant", result.content)
                return result.content

            # Handle tool calls
            # 1. Add model's assistant message (containing tool calls) to the thread
            messages.append(
                ChatMessage(
                    role="assistant", content=result.content, tool_calls=result.tool_calls
                )
            )

            # 2. Execute each tool and add tool results
            for tc in result.tool_calls:
                tool_output = await execute_tool(tc.name, tc.arguments)
                messages.append(
                    ChatMessage(
                        role="tool",
                        content=tool_output,
                        tool_result=ToolResult(call_id=tc.call_id, name=tc.name, content=tool_output),
                    )
                )

        return "Error: Maximum tool iterations reached."

    async def send_message_stream(
        self,
        text: str,
        session: Session,
        media: list[MediaPart] | None = None,
        user_name: str | None = None,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Send a message and stream response chunks. 
        Note: Currently Gemini streaming doesn't support tools in the same way 
        as non-streaming in some SDKs, but we'll implement it as a loop.
        If a tool call is detected, we stop streaming and process the tool.
        """
        # For simplicity in Phase 1, if tools are possible, we might fallback to non-streaming 
        # for the tool part, or just handle it in the loop.
        # But wait, send_message_stream is used by the UI for that typing effect.
        # Let's implement a loop that streams text, but if it's a tool call, 
        # it handles it and then continues.

        messages = self._build_messages(text, session, media, user_name)

        max_iterations = 5
        for _ in range(max_iterations):
            # We use non-streaming for tool-capable turns to simplify
            # (Gemma 4 streaming with tools can be tricky over raw HTTP)
            result = await self.provider.generate(messages, tools=TOOLS_METADATA)

            if not result.tool_calls:
                # Stream the final content in one go (or chunks if we had a real streamer)
                # Since we called 'generate', we have the full content.
                # To simulate streaming for the UI:
                words = result.content.split(" ")
                current = ""
                for i, word in enumerate(words):
                    current += (word + " ") if i < len(words) - 1 else word
                    yield current, result.model_used
                    await asyncio.sleep(0.02)

                session.add_message("assistant", result.content)
                return

            # Tool calls detected
            # Show a "Thinking..." or tool hint in the stream?
            yield f" (Using {result.tool_calls[0].name}...)", result.model_used

            messages.append(
                ChatMessage(
                    role="assistant", content=result.content, tool_calls=result.tool_calls
                )
            )

            for tc in result.tool_calls:
                tool_output = await execute_tool(tc.name, tc.arguments)
                messages.append(
                    ChatMessage(
                        role="tool",
                        content=tool_output,
                        tool_result=ToolResult(call_id=tc.call_id, name=tc.name, content=tool_output),
                    )
                )

    def _build_messages(
        self,
        text: str,
        session: Session,
        media: list[MediaPart] | None = None,
        user_name: str | None = None,
    ) -> list[ChatMessage]:
        """Prepare message list for the provider."""
        builder = ContextBuilder(user_name=user_name, memory_store=self.memory)
        system_prompt = builder.build()
        self.provider.system_instruction = system_prompt

        messages = []
        # Add history
        for msg in session.messages:
            messages.append(ChatMessage(role=msg.role, content=msg.content))

        # Add current message
        messages.append(ChatMessage(role="user", content=text, media=media))
        return messages

    async def archive_conversation(self, session: Session) -> None:
        """Summarise and archive a session's messages to memory history.

        Uses the AI to distill key facts and a concise summary.
        """
        if not session.messages or len(session.messages) < 2:
            return

        try:
            summary, new_facts = await self._summarize_and_extract(session)

            # Update long-term facts
            if new_facts:
                self._memory.add_facts(new_facts)

            # Update history summary
            if summary:
                self._memory.append_history(summary)
                self._memory.compact_history()

            logger.info("Archived session %s to memory", session.id)
        except Exception as e:
            logger.error("Failed to archive conversation %s: %s", session.id, e)

    async def _summarize_and_extract(self, session: Session) -> tuple[str, list[str]]:
        """Use Gemma to distill the conversation into a summary and facts."""
        transcript = []
        for m in session.messages:
            transcript.append(f"{m.role.upper()}: {m.content}")

        prompt = (
            "Analyze the following conversation transcript. Respond ONLY with a JSON object containing:\n"
            '1. "summary": A concise 1-sentence summary of the exchange.\n'
            '2. "facts": A list of new key facts about the user (preferences, names, location, goals) '
            "discovered in this chat. Keep facts short.\n\n"
            "TRANSCRIPT:\n" + "\n".join(transcript)
        )

        try:
            # We use the provider directly for this internal task
            result = await self.provider.generate([ChatMessage(role="user", content=prompt)])
            # Basic JSON extraction
            content = result.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(content)
            return data.get("summary", ""), data.get("facts", [])
        except Exception as e:
            logger.warning("Summarization failed, falling back to manual: %s", e)
            first_q = session.messages[0].content[:100]
            return f"User asked about: {first_q}", []
