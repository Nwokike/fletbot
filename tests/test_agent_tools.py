import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.agent.runner import AgentRunner
from src.providers.base import ChatMessage, GenerationResult, ToolCall, ToolResult
from src.session.manager import Session
from src.agent.tools import WebTools, execute_tool


@pytest.mark.asyncio
async def test_web_search_success():
    with patch("src.agent.tools.DDGS") as mock_ddgs:
        mock_instance = mock_ddgs.return_value.__enter__.return_value
        mock_instance.text.return_value = [
            {"title": "Test Result", "href": "https://test.com", "body": "This is a test"}
        ]
        
        result = await WebTools.web_search("test query")
        assert "Test Result" in result
        assert "https://test.com" in result
        assert "This is a test" in result


@pytest.mark.asyncio
async def test_web_fetch_success():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = "<html><body><h1>Hello World</h1><p>This is a test.</p></body></html>"
        mock_get.return_value = mock_response
        
        result = await WebTools.web_fetch("https://example.com")
        assert "# Hello World" in result
        assert "This is a test." in result


@pytest.mark.asyncio
async def test_agent_runner_tool_loop():
    # Mock provider
    mock_provider = MagicMock()
    # First call returns a tool call
    result1 = GenerationResult(
        content="Let me search for that.",
        model_used="Gemma 4",
        tool_calls=[ToolCall(call_id="web_search", name="web_search", arguments={"query": "weather"})]
    )
    # Second call returns the final answer
    result2 = GenerationResult(
        content="The weather is sunny.",
        model_used="Gemma 4"
    )
    
    mock_provider.generate = AsyncMock(side_effect=[result1, result2])
    
    # Mock tool execution
    with patch("src.agent.runner.execute_tool", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "Sunny, 25C"
        
        runner = AgentRunner(provider=mock_provider)
        session = Session(id="test", messages=[])
        session.add_message("user", "What's the weather?")
        
        response = await runner.send_message("What's the weather?", session)
        
        assert response == "The weather is sunny."
        assert len(session.messages) == 2 # assistant response is added
        assert mock_exec.called
        assert mock_exec.call_args[0][0] == "web_search"
        assert mock_exec.call_args[0][1] == {"query": "weather"}


@pytest.mark.asyncio
async def test_execute_tool_dispatcher():
    with patch("src.agent.tools.WebTools.web_search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = "Search result"
        res = await execute_tool("web_search", {"query": "test"})
        assert res == "Search result"
        mock_search.assert_called_once_with(query="test")

    with patch("src.agent.tools.WebTools.web_fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = "Fetch result"
        res = await execute_tool("web_fetch", {"url": "https://test.com"})
        assert res == "Fetch result"
        mock_fetch.assert_called_once_with(url="https://test.com")
