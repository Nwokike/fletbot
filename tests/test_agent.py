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
    # Now send_message_stream uses provider.generate internally for Phase 1 tools
    result = GenerationResult(content="Hello World", model_used="Gemma 4")
    mock_provider.generate = AsyncMock(return_value=result)
    
    runner = AgentRunner(mock_provider)
    from src.session.manager import Session
    session = Session()
    
    results = []
    async for chunk, model in runner.send_message_stream("Test", session):
        results.append(chunk)
        
    assert "Hello" in results[0]
    assert results[-1].strip() == "Hello World"
