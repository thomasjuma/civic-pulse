from app.agents import mcp_servers


class FakeMCPServerStdio:
    def __init__(self, name: str, params: dict, client_session_timeout_seconds: float) -> None:
        self.name = name
        self.params = params
        self.client_session_timeout_seconds = client_session_timeout_seconds


def test_create_playwright_mcp_server_without_docker(monkeypatch) -> None:
    monkeypatch.setattr(mcp_servers, "MCPServerStdio", FakeMCPServerStdio)
    monkeypatch.setattr(mcp_servers.os.path, "exists", lambda path: False)
    monkeypatch.delenv("AWS_EXECUTION_ENV", raising=False)

    server = mcp_servers.create_playwright_mcp_server(timeout_seconds=12)

    assert server.name == "playwright"
    assert server.params["command"] == "npx"
    assert "--executable-path" not in server.params["args"]
    assert server.client_session_timeout_seconds == 12


def test_create_playwright_mcp_server_uses_found_chrome_in_docker(monkeypatch) -> None:
    monkeypatch.setattr(mcp_servers, "MCPServerStdio", FakeMCPServerStdio)
    monkeypatch.setattr(mcp_servers.os.path, "exists", lambda path: True)
    monkeypatch.setattr(mcp_servers.glob, "glob", lambda pattern: ["/chrome"])

    server = mcp_servers.create_playwright_mcp_server()

    assert server.params["args"][-2:] == ["--executable-path", "/chrome"]


def test_create_playwright_mcp_server_uses_fallback_chrome(monkeypatch) -> None:
    monkeypatch.setattr(mcp_servers, "MCPServerStdio", FakeMCPServerStdio)
    monkeypatch.setattr(mcp_servers.os.path, "exists", lambda path: False)
    monkeypatch.setenv("AWS_EXECUTION_ENV", "lambda")
    monkeypatch.setattr(mcp_servers.glob, "glob", lambda pattern: [])

    server = mcp_servers.create_playwright_mcp_server()

    assert server.params["args"][-2] == "--executable-path"
    assert "chromium-1208" in server.params["args"][-1]


def test_create_pdf_reader_and_combined_servers(monkeypatch) -> None:
    monkeypatch.setattr(mcp_servers, "MCPServerStdio", FakeMCPServerStdio)
    monkeypatch.setattr(mcp_servers.os.path, "exists", lambda path: False)
    monkeypatch.delenv("AWS_EXECUTION_ENV", raising=False)

    pdf_server = mcp_servers.create_pdf_reader_mcp_server(timeout_seconds=9)
    servers = mcp_servers.create_browser_agent_mcp_servers(timeout_seconds=8)

    assert pdf_server.name == "pdf-reader"
    assert pdf_server.params == {"command": "uvx", "args": ["mcp-pdf-reader"]}
    assert pdf_server.client_session_timeout_seconds == 9
    assert [server.name for server in servers] == ["playwright", "pdf-reader"]
    assert all(server.client_session_timeout_seconds == 8 for server in servers)

