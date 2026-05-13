import pytest

from app.agents import tools
from app.models import Article, Subscriber


def _article() -> Article:
    return Article(
        id=11,
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
        id=6,
        clerk_user_id=None,
        email="reader@example.com",
        whatsapp_number="254700000000",
        has_whatsapp_consent=True,
        consented_at="2026-05-13T00:00:00+00:00",
    )


def test_whatsapp_message_formats_summary() -> None:
    assert tools._whatsapp_message("Title", "Source", "Summary") == "Civic Pulse Summary\n\nTitle\nSource: Source\n\nSummary"


def test_save_article_summary_record_success_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "save_article_summary", lambda article: _article())

    result = tools.save_article_summary_record(
        title="Audit Report",
        source="oagkenya.go.ke",
        summary="A formal summary.",
        full_text="Complete text.",
        date="2026-05-13",
    )

    assert result["article_id"] == 11

    monkeypatch.setattr(tools, "save_article_summary", lambda article: (_ for _ in ()).throw(RuntimeError("save failed")))
    with pytest.raises(RuntimeError, match="save failed"):
        tools.save_article_summary_record("Title", "Source", "Summary", "Text", "")


@pytest.mark.asyncio
async def test_decorated_tool_wrappers_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    class Context:
        tool_name = "tool"
        run_config = None

    monkeypatch.setattr(
        tools,
        "save_article_summary_record",
        lambda **kwargs: {"saved": True, "article_id": 1, "title": kwargs["title"], "source": kwargs["source"]},
    )

    save_result = await tools.save_article_summary_tool.on_invoke_tool(
        Context(),
        '{"title":"Title","source":"Source","summary":"Summary","full_text":"Text","date":"2026-05-13"}',
    )

    assert save_result["article_id"] == 1

    async def send_whatsapp_summary(**kwargs):
        return {"article_id": kwargs["article_id"], "recipients_found": 1, "messages_sent": 1}

    monkeypatch.setattr(tools, "send_whatsapp_summary", send_whatsapp_summary)

    send_result = await tools.send_whatsapp_summary_tool.on_invoke_tool(
        Context(),
        '{"article_id":1,"title":"Title","source":"Source","summary":"Summary"}',
    )

    assert send_result["messages_sent"] == 1


@pytest.mark.asyncio
async def test_send_whatsapp_summary_no_recipients(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "get_pending_whatsapp_recipients", lambda article_id: [])

    result = await tools.send_whatsapp_summary(1, "Title", "Source", "Summary")

    assert result == {"article_id": 1, "recipients_found": 0, "messages_sent": 0}


@pytest.mark.asyncio
async def test_send_whatsapp_summary_success_false_send_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    marked: list[tuple[int, int]] = []

    class FakeWhatsAppClient:
        responses = [True, False]

        async def send_text(self, recipient_number: str, message: str) -> bool:
            return self.responses.pop(0)

    monkeypatch.setattr(tools, "get_pending_whatsapp_recipients", lambda article_id: [_subscriber(), _subscriber()])
    monkeypatch.setattr(tools, "mark_whatsapp_summary_sent", lambda article_id, subscriber_id: marked.append((article_id, subscriber_id)))
    monkeypatch.setattr(tools, "WhatsAppClient", lambda: FakeWhatsAppClient())

    result = await tools.send_whatsapp_summary(1, "Title", "Source", "Summary")

    assert result["recipients_found"] == 2
    assert result["messages_sent"] == 1
    assert marked == [(1, 6)]

    monkeypatch.setattr(tools, "get_pending_whatsapp_recipients", lambda article_id: (_ for _ in ()).throw(RuntimeError("lookup failed")))
    with pytest.raises(RuntimeError, match="lookup failed"):
        await tools.send_whatsapp_summary(1, "Title", "Source", "Summary")

    class FailingWhatsAppClient:
        async def send_text(self, recipient_number: str, message: str) -> bool:
            raise RuntimeError("send failed")

    monkeypatch.setattr(tools, "get_pending_whatsapp_recipients", lambda article_id: [_subscriber()])
    monkeypatch.setattr(tools, "WhatsAppClient", lambda: FailingWhatsAppClient())
    with pytest.raises(RuntimeError, match="send failed"):
        await tools.send_whatsapp_summary(1, "Title", "Source", "Summary")

    class SuccessfulWhatsAppClient:
        async def send_text(self, recipient_number: str, message: str) -> bool:
            return True

    monkeypatch.setattr(tools, "WhatsAppClient", lambda: SuccessfulWhatsAppClient())
    monkeypatch.setattr(tools, "mark_whatsapp_summary_sent", lambda article_id, subscriber_id: (_ for _ in ()).throw(RuntimeError("mark failed")))
    with pytest.raises(RuntimeError, match="mark failed"):
        await tools.send_whatsapp_summary(1, "Title", "Source", "Summary")
