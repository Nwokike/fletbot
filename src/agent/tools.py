"""FletBot Tools — consumer-oriented toolset.

Includes:
- web_search: Search the web using DuckDuckGo (via ddgs).
- web_fetch: Fetch and extract markdown from URLs.
"""

import json
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from markdownify import markdownify as md


class WebTools:
    """Namespace for consumer web tools."""

    @staticmethod
    async def web_search(query: str, max_results: int = 5) -> str:
        """Search the web and return snippets."""
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_results)
                if not results:
                    return f"No results found for '{query}'."

                formatted = [f"Search results for: {query}\n"]
                for i, r in enumerate(results, 1):
                    title = r.get("title", "No Title")
                    link = r.get("href", "")
                    body = r.get("body", "")
                    formatted.append(f"{i}. {title}\n   {link}\n   {body}\n")
                return "\n".join(formatted)
        except Exception as e:
            return f"Error during web search: {str(e)}"

    @staticmethod
    async def web_fetch(url: str, max_chars: int = 20000) -> str:
        """Fetch a URL and convert its content to markdown."""
        try:
            # Basic URL validation
            if not url.startswith(("http://", "https://")):
                return "Error: Invalid URL. Must start with http:// or https://."

            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            # Check if content is HTML
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                # Return raw text if not HTML, truncated
                text = response.text
                return f"[Non-HTML content fetched from {url}]\n\n" + text[:max_chars]

            # Use BeautifulSoup to pre-process (remove scripts, styles)
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Convert to markdown
            markdown = md(str(soup), heading_style="ATX", bullets="-")

            # Clean up whitespace
            markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

            if len(markdown) > max_chars:
                markdown = markdown[:max_chars] + "\n\n... (content truncated)"

            return f"[Content from {url}]\n\n{markdown}"

        except Exception as e:
            return f"Error fetching {url}: {str(e)}"


# ── Tool Metadata ──────────────────────────────────────────────────

TOOLS_METADATA = [
    {
        "function_declarations": [
            {
                "name": "web_search",
                "description": "Search the web for current information, news, or facts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up.",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Number of results to return (default 5, max 10).",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "web_fetch",
                "description": "Fetch the full content of a specific web page and return it as markdown.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The absolute URL to fetch (e.g., https://example.com/page).",
                        },
                        "max_chars": {
                            "type": "integer",
                            "description": "Maximum characters to return (default 20,000).",
                        },
                    },
                    "required": ["url"],
                },
            },
        ]
    }
]


async def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """Dispatch and execute a tool by name."""
    if name == "web_search":
        return await WebTools.web_search(**arguments)
    elif name == "web_fetch":
        return await WebTools.web_fetch(**arguments)
    else:
        return f"Error: Tool '{name}' not found."
