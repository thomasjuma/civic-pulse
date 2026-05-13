from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from app.models import Subscriber, SubscriberUpsert
from app.routes import subscribers


@contextmanager
def _connection() -> Iterator[object]:
    yield object()


def test_save_subscriber_returns_saved_subscriber(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = SubscriberUpsert(
        email="reader@example.com",
        whatsapp_number="254700000000",
        has_whatsapp_consent=True,
    )
    expected = Subscriber(
        id=8,
        clerk_user_id=None,
        email="reader@example.com",
        whatsapp_number="254700000000",
        has_whatsapp_consent=True,
        consented_at="2026-05-13T00:00:00+00:00",
    )
    monkeypatch.setattr(subscribers, "get_connection", _connection)
    monkeypatch.setattr(subscribers, "upsert_subscriber", lambda connection, subscriber: expected)

    assert subscribers.save_subscriber(payload) == expected

