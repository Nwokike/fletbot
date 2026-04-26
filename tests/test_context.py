"""Tests for ContextBuilder — system prompt construction with memory injection."""

import pytest

from src.agent.context import ContextBuilder
from src.agent.memory import MemoryStore


@pytest.fixture
def memory(tmp_path):
    return MemoryStore(storage_dir=tmp_path)


class TestContextBuilder:
    def test_build_includes_datetime(self):
        """System prompt should include current date/time."""
        ctx = ContextBuilder()
        prompt = ctx.build()
        assert "UTC" in prompt
        assert "Current date and time" in prompt

    def test_build_includes_username_when_set(self):
        """User name should appear in the prompt when provided."""
        ctx = ContextBuilder(user_name="Alice")
        prompt = ctx.build()
        assert "Alice" in prompt

    def test_build_without_username(self):
        """Prompt should work fine without a username."""
        ctx = ContextBuilder()
        prompt = ctx.build()
        assert "FletBot" in prompt
        # Should NOT contain "user's name" placeholder
        assert "The user's name is" not in prompt

    def test_build_includes_memory_context(self, memory):
        """Long-term memory should be injected into the prompt."""
        memory.write_memory("User is a Python developer from Lagos")
        ctx = ContextBuilder(memory_store=memory)
        prompt = ctx.build()
        assert "Long-term Memory" in prompt
        assert "Python developer from Lagos" in prompt

    def test_build_includes_history_context(self, memory):
        """Recent history should be injected into the prompt."""
        memory.append_history("Discussed cooking tips")
        memory.append_history("Talked about Python async")
        ctx = ContextBuilder(memory_store=memory)
        prompt = ctx.build()
        assert "Recent Conversation History" in prompt
        assert "cooking tips" in prompt
        assert "Python async" in prompt

    def test_build_without_memory_store(self):
        """Should work cleanly with no memory store."""
        ctx = ContextBuilder()
        prompt = ctx.build()
        assert "Long-term Memory" not in prompt
        assert "Recent Conversation History" not in prompt

    def test_build_with_empty_memory(self, memory):
        """Empty memory should not add memory sections."""
        ctx = ContextBuilder(memory_store=memory)
        prompt = ctx.build()
        # No memory written, so no memory sections
        assert "Long-term Memory" not in prompt

    def test_build_includes_core_persona(self):
        """System prompt should include the core FletBot persona."""
        ctx = ContextBuilder()
        prompt = ctx.build()
        assert "FletBot" in prompt
        assert "friendly" in prompt
        assert "Gemma 4" in prompt

    def test_build_with_all_features(self, memory):
        """Full integration: username + memory + history."""
        memory.write_memory("User prefers dark mode")
        memory.append_history("Previous chat about weather")
        ctx = ContextBuilder(user_name="Bob", memory_store=memory)
        prompt = ctx.build()
        assert "Bob" in prompt
        assert "dark mode" in prompt
        assert "weather" in prompt
        assert "UTC" in prompt
