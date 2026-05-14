from pathlib import Path

import pytest

from app.config import Settings
from app.database import get_connection, init_db
from app.models import ArticleCreate, SubscriberUpsert
from app.repositories import (
    get_or_create_chat_conversation,
    list_chat_messages,
    mark_article_notification_sent,
    upsert_article,
    upsert_subscriber,
)
from app.services import chat


class FakeWhatsAppClient:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def send_text(self, recipient_number: str, message: str) -> bool:
        self.messages.append((recipient_number, message))
        return True


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        DATABASE_PATH=tmp_path / "test.db",
        OPENAI_API_KEY=None,
        WHATSAPP_ACCESS_TOKEN="token",
        WHATSAPP_PHONE_NUMBER_ID="phone-id",
    )


def test_extract_text_messages_ignores_non_text_messages() -> None:
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "+254 700-000-000",
                                    "id": "wamid.1",
                                    "type": "text",
                                    "text": {"body": " What does this mean? "},
                                },
                                {"from": "254700000000", "type": "image"},
                            ]
                        }
                    }
                ]
            }
        ]
    }

    assert chat.extract_text_messages(payload) == [
        chat.IncomingWhatsAppMessage(
            from_number="254700000000",
            text="What does this mean?",
            message_id="wamid.1",
        )
    ]


@pytest.mark.asyncio
async def test_handle_incoming_message_uses_latest_sent_article(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    init_db(settings)
    whatsapp_client = FakeWhatsAppClient()

    with get_connection(settings) as connection:
        article = upsert_article(
            connection,
            ArticleCreate(
                title="Appropriation Bill",
                source="parliament.go.ke",
                source_url="https://example.test/bill",
                summary="A formal summary.",
                full_text="The complete bill text.",
                date="2026-05-14",
                image="",
            ),
        )
        subscriber = upsert_subscriber(
            connection,
            SubscriberUpsert(
                email="reader@example.com",
                whatsapp_number="254700000000",
                has_whatsapp_consent=True,
            ),
        )
        mark_article_notification_sent(connection, article.id, subscriber.id)

    sent = await chat.handle_incoming_message(
        chat.IncomingWhatsAppMessage("254700000000", "What is the key point?", "wamid.1"),
        settings,
        whatsapp_client,
    )

    with get_connection(settings) as connection:
        conversation_id = get_or_create_chat_conversation(connection, subscriber.id, article.id)
        messages = list_chat_messages(connection, conversation_id)

    assert sent is True
    assert whatsapp_client.messages[0][0] == "254700000000"
    assert "AI chat service is not configured" in whatsapp_client.messages[0][1]
    assert messages[0] == {"role": "user", "content": "What is the key point?"}
    assert messages[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_handle_whatsapp_webhook_returns_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    async def handle_incoming_message(incoming_message):
        assert incoming_message.text == "Hello"
        return True

    monkeypatch.setattr(chat, "handle_incoming_message", handle_incoming_message)

    result = await chat.handle_whatsapp_webhook(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "254700000000",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    )

    assert result.received_messages == 1
    assert result.replies_sent == 1
