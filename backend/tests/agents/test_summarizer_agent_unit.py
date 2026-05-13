import sys
import types

import pytest

from app.agents import summarizer_agent
from app.models import Article, Subscriber


def _article() -> Article:
    return Article(
        id=4,
        title="Audit Report",
        source="oagkenya.go.ke",
        source_url="https://example.test/report",
        summary="A formal summary.",
        full_text="Complete text.",
        date="2026-05-13",
        image="",
    )


def _subscriber() -> Subscriber:
    return Subscriber(
        id=2,
        clerk_user_id=None,
        email="reader@example.com",
        whatsapp_number="254700000000",
        has_whatsapp_consent=True,
        consented_at="2026-05-13T00:00:00+00:00",
    )


def test_fallback_summary_short_and_truncated_text() -> None:
    assert summarizer_agent._fallback_summary("short text") == "short text"
    assert summarizer_agent._fallback_summary("one two three four", max_chars=9) == "one two..."


def test_parse_agent_output_variants() -> None:
    structured = summarizer_agent.SummaryAgentOutput(
        summary="Summary",
        article_id=3,
        whatsapp_messages_sent=2,
    )
    assert summarizer_agent._parse_agent_output(structured).article_id == 3

    parsed = summarizer_agent._parse_agent_output(
        '```json\n{"summary":"Summary","article_id":5,"whatsapp_messages_sent":1}\n```'
    )
    assert parsed.summary == "Summary"
    assert parsed.article_id == 5
    assert parsed.whatsapp_messages_sent == 1

    assert summarizer_agent._parse_agent_output("not-json").summary == "not-json"
    assert summarizer_agent._parse_agent_output("[1]").summary == "[1]"
    defaults = summarizer_agent._parse_agent_output('{"summary":"Summary","article_id":"bad"}')
    assert defaults.article_id is None
    assert defaults.whatsapp_messages_sent == 0


@pytest.mark.asyncio
async def test_publish_without_openai_saves_and_sends(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[tuple[str, str]] = []
    marked: list[tuple[int, int]] = []

    class FakeWhatsAppClient:
        async def send_text(self, recipient_number: str, message: str) -> bool:
            sent.append((recipient_number, message))
            return True

    monkeypatch.setattr(summarizer_agent, "save_article_summary", lambda article: _article())
    monkeypatch.setattr(summarizer_agent, "get_pending_whatsapp_recipients", lambda article_id: [_subscriber()])
    monkeypatch.setattr(summarizer_agent, "mark_whatsapp_summary_sent", lambda article_id, subscriber_id: marked.append((article_id, subscriber_id)))
    monkeypatch.setattr(summarizer_agent, "WhatsAppClient", lambda: FakeWhatsAppClient())

    result = await summarizer_agent._publish_without_openai(
        title="Audit Report",
        source="oagkenya.go.ke",
        full_text="Complete text.",
        date="2026-05-13",
        image="",
        source_url="https://example.test/report",
    )

    assert result.article_id == 4
    assert result.whatsapp_messages_sent == 1
    assert sent[0][0] == "254700000000"
    assert marked == [(4, 2)]


@pytest.mark.asyncio
async def test_publish_without_openai_reraises_save_and_send_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(summarizer_agent, "save_article_summary", lambda article: (_ for _ in ()).throw(RuntimeError("save failed")))

    with pytest.raises(RuntimeError, match="save failed"):
        await summarizer_agent._publish_without_openai("Title", "Source", "Text", "", "", None)

    monkeypatch.setattr(summarizer_agent, "save_article_summary", lambda article: _article())
    monkeypatch.setattr(summarizer_agent, "get_pending_whatsapp_recipients", lambda article_id: (_ for _ in ()).throw(RuntimeError("send failed")))

    with pytest.raises(RuntimeError, match="send failed"):
        await summarizer_agent._publish_without_openai("Title", "Source", "Text", "", "", None)


@pytest.mark.asyncio
async def test_summarize_and_publish_uses_fallback_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    async def publish_without_openai(*args, **kwargs):
        return summarizer_agent.SummaryPublishResult("Summary", 1, 0)

    monkeypatch.setattr(summarizer_agent, "_publish_without_openai", publish_without_openai)

    result = await summarizer_agent.summarize_and_publish_document("Title", "Source", "Text", "", "", None)

    assert result.summary == "Summary"


@pytest.mark.asyncio
async def test_summarize_and_publish_uses_fallback_when_sdk_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setitem(sys.modules, "agents", None)

    async def publish_without_openai(*args, **kwargs):
        return summarizer_agent.SummaryPublishResult("Summary", 1, 0)

    monkeypatch.setattr(summarizer_agent, "_publish_without_openai", publish_without_openai)

    result = await summarizer_agent.summarize_and_publish_document("Title", "Source", "Text", "", "", None)

    assert result.article_id == 1


@pytest.mark.asyncio
async def test_summarize_and_publish_uses_agent_and_reraises_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "key")

    class FakeAgent:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    class FakeRunner:
        should_raise = False

        @staticmethod
        async def run(agent: FakeAgent, prompt: str):
            if FakeRunner.should_raise:
                raise RuntimeError("agent failed")
            assert agent.kwargs["output_type"] is summarizer_agent.SummaryAgentOutput
            return types.SimpleNamespace(final_output='{"summary":"Summary","article_id":8,"whatsapp_messages_sent":4}')

    monkeypatch.setitem(sys.modules, "agents", types.SimpleNamespace(Agent=FakeAgent, Runner=FakeRunner))

    result = await summarizer_agent.summarize_and_publish_document("Title", "Source", "Text", "", "", None)

    assert result.article_id == 8
    assert result.whatsapp_messages_sent == 4

    FakeRunner.should_raise = True
    with pytest.raises(RuntimeError, match="agent failed"):
        await summarizer_agent.summarize_and_publish_document("Title", "Source", "Text", "", "", None)


@pytest.mark.asyncio
async def test_summarize_document_fallback_and_agent_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert await summarizer_agent.summarize_document("Title", "Source", "Text") == "Text"

    monkeypatch.setenv("OPENAI_API_KEY", "key")

    class FakeAgent:
        def __init__(self, **kwargs) -> None:
            pass

    class FakeRunner:
        should_raise = False

        @staticmethod
        async def run(agent: FakeAgent, prompt: str):
            if FakeRunner.should_raise:
                raise RuntimeError("draft failed")
            return types.SimpleNamespace(final_output="Draft summary")

    monkeypatch.setitem(sys.modules, "agents", types.SimpleNamespace(Agent=FakeAgent, Runner=FakeRunner))

    assert await summarizer_agent.summarize_document("Title", "Source", "Text") == "Draft summary"

    FakeRunner.should_raise = True
    with pytest.raises(RuntimeError, match="draft failed"):
        await summarizer_agent.summarize_document("Title", "Source", "Text")


@pytest.mark.asyncio
async def test_summarize_document_uses_fallback_when_sdk_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setitem(sys.modules, "agents", None)

    assert await summarizer_agent.summarize_document("Title", "Source", "Text") == "Text"
