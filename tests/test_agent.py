import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent.runner import AgentRunner
from src.agent.context import ContextBuilder
from src.providers.base import ChatMessage, GenerationResult

def test_context_builder_basic():
    builder = ContextBuilder()
    prompt = builder.build()
    assert "FletBot" in prompt
    assert "Gemma 4" in prompt

def test_context_builder_with_user():
    builder = ContextBuilder(user_name="John")
    prompt = builder.build()
    assert "John" in prompt

@pytest.mark.asyncio
async def test_agent_runner_success():
    mock_provider = MagicMock()
    # generate_stream is a function that returns an async generator
    # So we use side_effect with an async generator function
    async def mock_stream(*args, **kwargs):
        yield "Part 1", "Gemma 4"
        yield "Part 2", "Gemma 4"
        
    mock_provider.generate_stream.side_effect = mock_stream
    
    runner = AgentRunner(mock_provider)
    from src.session.manager import Session
    session = Session()
    
    results = []
    async for chunk, model in runner.send_message_stream("Test", session):
        results.append(chunk)
        
    assert results == ["Part 1", "Part 2"]
