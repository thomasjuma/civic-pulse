import pytest

from app.config import Settings
from app.services import whatsapp


def _settings(**overrides) -> Settings:
    values = {
        "DATABASE_PATH": ":memory:",
        "WHATSAPP_ACCESS_TOKEN": "token",
        "WHATSAPP_PHONE_NUMBER_ID": "phone-id",
        "WHATSAPP_API_VERSION": "v20.0",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.asyncio
async def test_send_text_returns_false_without_credentials() -> None:
    client = whatsapp.WhatsAppClient(
        _settings(
            WHATSAPP_ACCESS_TOKEN=None,
            WHATSAPP_PHONE_NUMBER_ID=None,
        )
    )

    assert await client.send_text("254700000000", "Message") is False


@pytest.mark.asyncio
async def test_send_text_posts_to_whatsapp_api(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []

    class Response:
        def raise_for_status(self) -> None:
            calls.append({"raised": False})

    class AsyncClient:
        def __init__(self, timeout: float) -> None:
            assert timeout == 30.0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, url: str, json: dict, headers: dict) -> Response:
            calls.append({"url": url, "json": json, "headers": headers})
            return Response()

    monkeypatch.setattr(whatsapp.httpx, "AsyncClient", AsyncClient)
    client = whatsapp.WhatsAppClient(_settings())

    assert await client.send_text("254700000000", "Message") is True
    assert calls[0]["url"] == "https://graph.facebook.com/v20.0/phone-id/messages"
    assert calls[0]["json"]["to"] == "254700000000"
    assert calls[0]["json"]["text"]["body"] == "Message"
    assert calls[0]["headers"] == {"Authorization": "Bearer token"}
    assert calls[1] == {"raised": False}


@pytest.mark.asyncio
async def test_send_text_reraises_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            raise RuntimeError("bad response")

    class AsyncClient:
        def __init__(self, timeout: float) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, url: str, json: dict, headers: dict) -> Response:
            return Response()

    monkeypatch.setattr(whatsapp.httpx, "AsyncClient", AsyncClient)
    client = whatsapp.WhatsAppClient(_settings())

    with pytest.raises(RuntimeError, match="bad response"):
        await client.send_text("254700000000", "Message")

