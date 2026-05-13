import sys
import types

import pytest

from app.agents import browser_agent


def _valid_payload() -> str:
    return (
        '[{"title":"Report","source":"oagkenya.go.ke","source_url":"https://example.test",'
        '"date":"2026-05-13","image":"","full_text":"Complete text"}]'
    )


def test_documents_from_json_parses_valid_and_fenced_payloads() -> None:
    documents = browser_agent._documents_from_json(f"```json\n{_valid_payload()}\n```", limit=5)

    assert len(documents) == 1
    assert documents[0].title == "Report"


def test_documents_from_json_parses_plain_fenced_payload() -> None:
    documents = browser_agent._documents_from_json(f"```\n{_valid_payload()}\n```", limit=5)

    assert len(documents) == 1


def test_documents_from_json_handles_invalid_non_list_and_missing_fields() -> None:
    assert browser_agent._documents_from_json("not-json", limit=5) == []
    assert browser_agent._documents_from_json('{"title":"Report"}', limit=5) == []
    assert browser_agent._documents_from_json('[{"title":"Report"}]', limit=5) == []
    assert browser_agent._documents_from_json(f"[1, {_valid_payload()[1:-1]}]", limit=1)[0].title == "Report"


def test_document_from_mapping_accepts_url_alias_and_strips_values() -> None:
    document = browser_agent._document_from_mapping(
        {
            "title": " Report ",
            "source": " parliament.go.ke ",
            "url": " https://example.test/bill ",
            "date": " 2026-05-13 ",
            "image": " ",
            "full_text": " Text ",
        }
    )

    assert document is not None
    assert document.source_url == "https://example.test/bill"
    assert document.full_text == "Text"


@pytest.mark.asyncio
async def test_retrieve_latest_documents_returns_empty_without_sources_or_key(monkeypatch: pytest.MonkeyPatch) -> None:
    assert await browser_agent.retrieve_latest_documents((), limit=5) == []

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert await browser_agent.retrieve_latest_documents(("https://example.test",), limit=5) == []


@pytest.mark.asyncio
async def test_retrieve_latest_documents_returns_empty_when_sdk_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setitem(sys.modules, "agents", None)

    assert await browser_agent.retrieve_latest_documents(("https://example.test",), limit=5) == []


@pytest.mark.asyncio
async def test_retrieve_latest_documents_runs_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setattr(browser_agent, "create_browser_agent_mcp_servers", lambda timeout_seconds: ["server"])

    class FakeAgent:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    class FakeRunner:
        @staticmethod
        async def run(agent: FakeAgent, prompt: str):
            assert agent.kwargs["mcp_servers"] == ["active-server"]
            assert "https://example.test" in prompt
            return types.SimpleNamespace(final_output=_valid_payload())

    class FakeMCPServerManager:
        def __init__(self, servers, **kwargs) -> None:
            assert servers == ["server"]
            self.active_servers = ["active-server"]

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

    monkeypatch.setitem(sys.modules, "agents", types.SimpleNamespace(Agent=FakeAgent, Runner=FakeRunner))
    monkeypatch.setitem(sys.modules, "agents.mcp", types.SimpleNamespace(MCPServerManager=FakeMCPServerManager))

    documents = await browser_agent.retrieve_latest_documents(("https://example.test",), limit=5)

    assert len(documents) == 1
    assert documents[0].title == "Report"


@pytest.mark.asyncio
async def test_retrieve_latest_documents_reraises_agent_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setattr(browser_agent, "create_browser_agent_mcp_servers", lambda timeout_seconds: ["server"])

    class FakeAgent:
        def __init__(self, **kwargs) -> None:
            pass

    class FakeRunner:
        @staticmethod
        async def run(agent: FakeAgent, prompt: str):
            raise RuntimeError("agent failed")

    class FakeMCPServerManager:
        active_servers = []

        def __init__(self, servers, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

    monkeypatch.setitem(sys.modules, "agents", types.SimpleNamespace(Agent=FakeAgent, Runner=FakeRunner))
    monkeypatch.setitem(sys.modules, "agents.mcp", types.SimpleNamespace(MCPServerManager=FakeMCPServerManager))

    with pytest.raises(RuntimeError, match="agent failed"):
        await browser_agent.retrieve_latest_documents(("https://example.test",), limit=5)
