from pathlib import Path

import pytest

from app.agents import tools
from app.config import Settings
from app.database import get_connection, init_db
from app.models import ArticleCreate, SubscriberUpsert
from app.repositories import list_consenting_subscribers, upsert_article, upsert_subscriber


def _settings(tmp_path: Path) -> Settings:
    return Settings(DATABASE_PATH=tmp_path / "test.db")


@pytest.mark.asyncio
async def test_send_whatsapp_summary_tool_marks_successful_sends(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    init_db(settings)

    with get_connection(settings) as connection:
        article = upsert_article(
            connection,
            ArticleCreate(
                title="Finance Bill",
                source="parliament.go.ke",
                source_url="https://example.test/bill",
                summary="A formal summary.",
                full_text="The complete bill text.",
                date="2026-05-13",
                image="",
            ),
        )
        upsert_subscriber(
            connection,
            SubscriberUpsert(
                email="reader@example.com",
                whatsapp_number="254700000000",
                has_whatsapp_consent=True,
            ),
        )

    monkeypatch.setattr(tools, "get_pending_whatsapp_recipients", lambda article_id: _recipients(settings, article_id))
    monkeypatch.setattr(tools, "mark_whatsapp_summary_sent", lambda article_id, subscriber_id: _mark_sent(settings, article_id, subscriber_id))
    monkeypatch.setattr(tools, "WhatsAppClient", lambda: _FakeWhatsAppClient())

    result = await tools.send_whatsapp_summary(
        article_id=1,
        title="Finance Bill",
        source="parliament.go.ke",
        summary="A formal summary.",
    )

    assert result["messages_sent"] == 1
    with get_connection(settings) as connection:
        assert list_consenting_subscribers(connection, article.id) == []


def _recipients(settings: Settings, article_id: int):
    with get_connection(settings) as connection:
        return list_consenting_subscribers(connection, article_id)


def _mark_sent(settings: Settings, article_id: int, subscriber_id: int) -> None:
    from app.repositories import mark_article_notification_sent

    with get_connection(settings) as connection:
        mark_article_notification_sent(connection, article_id, subscriber_id)


class _FakeWhatsAppClient:
    async def send_text(self, recipient_number: str, message: str) -> bool:
        assert recipient_number == "254700000000"
        assert "Finance Bill" in message
        return True
