"""MCP server configurations for browser-agent document retrieval."""

import glob
import os

from agents.mcp import MCPServerStdio


def create_playwright_mcp_server(timeout_seconds: float = 60) -> MCPServerStdio:
    """Create a Playwright MCP server instance for web browsing.

    Args:
        timeout_seconds: Client session timeout in seconds (default: 60)

    Returns:
        MCPServerStdio instance configured for Playwright
    """
    args = [
        "@playwright/mcp@latest",
        "--headless",
        "--isolated",
        "--no-sandbox",
        "--ignore-https-errors",
        "--user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    ]

    if os.path.exists("/.dockerenv") or os.environ.get("AWS_EXECUTION_ENV"):
        chrome_paths = glob.glob("/root/.cache/ms-playwright/chromium-*/chrome-linux*/chrome")
        if chrome_paths:
            chrome_path = chrome_paths[0]
            print(f"DEBUG: Found Chrome at: {chrome_path}")
            args.extend(["--executable-path", chrome_path])
        else:
            print("DEBUG: Chrome not found via glob, using fallback path")
            args.extend(["--executable-path", "/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"])

    return MCPServerStdio(
        name="playwright",
        params={"command": "npx", "args": args},
        client_session_timeout_seconds=timeout_seconds,
    )


def create_pdf_reader_mcp_server(timeout_seconds: float = 60) -> MCPServerStdio:
    """Create a PDF Reader MCP server for extracting text from PDF files."""
    return MCPServerStdio(
        name="pdf-reader",
        params={"command": "uvx", "args": ["mcp-pdf-reader"]},
        client_session_timeout_seconds=timeout_seconds,
    )


def create_browser_agent_mcp_servers(timeout_seconds: float = 60) -> list[MCPServerStdio]:
    """Create all MCP servers needed by the browser agent."""
    return [
        create_playwright_mcp_server(timeout_seconds),
        create_pdf_reader_mcp_server(timeout_seconds),
    ]
