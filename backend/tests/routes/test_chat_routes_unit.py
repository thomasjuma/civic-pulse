import pytest
from fastapi import HTTPException

from app.config import Settings
from app.routes import chat
from app.services.chat import ChatWebhookResult


def test_verify_whatsapp_webhook_returns_challenge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        chat,
        "get_settings",
        lambda: Settings(DATABASE_PATH=":memory:", WHATSAPP_VERIFY_TOKEN="secret"),
    )

    assert chat.verify_whatsapp_webhook("subscribe", "secret", "challenge") == "challenge"


def test_verify_whatsapp_webhook_rejects_bad_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        chat,
        "get_settings",
        lambda: Settings(DATABASE_PATH=":memory:", WHATSAPP_VERIFY_TOKEN="secret"),
    )

    with pytest.raises(HTTPException) as error:
        chat.verify_whatsapp_webhook("subscribe", "wrong", "challenge")

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_receive_whatsapp_webhook_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    class Request:
        async def json(self) -> dict:
            return {"entry": []}

    async def handle_whatsapp_webhook(payload: dict) -> ChatWebhookResult:
        assert payload == {"entry": []}
        return ChatWebhookResult(received_messages=0, replies_sent=0)

    monkeypatch.setattr(chat, "handle_whatsapp_webhook", handle_whatsapp_webhook)

    assert await chat.receive_whatsapp_webhook(Request()) == ChatWebhookResult(
        received_messages=0,
        replies_sent=0,
    )
