from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from app.models import Article, ArticleCreate, Subscriber
from app.services import database_service


@contextmanager
def _connection() -> Iterator[object]:
    yield object()


def _article() -> ArticleCreate:
    return ArticleCreate(
        title="Audit Report",
        source="oagkenya.go.ke",
        source_url="https://example.test/report",
        summary="A formal summary.",
        full_text="The complete report text.",
        date="2026-05-13",
        image="",
    )


def test_save_article_summary_returns_saved_article(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = Article(id=7, **_article().model_dump())
    monkeypatch.setattr(database_service, "get_connection", _connection)
    monkeypatch.setattr(database_service, "upsert_article", lambda connection, article: expected)

    assert database_service.save_article_summary(_article()) == expected


def test_save_article_summary_logs_and_reraises_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_service, "get_connection", _connection)

    def raise_error(connection: object, article: ArticleCreate) -> Article:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(database_service, "upsert_article", raise_error)

    with pytest.raises(RuntimeError, match="database unavailable"):
        database_service.save_article_summary(_article())


def test_get_pending_whatsapp_recipients_returns_subscribers(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = [
        Subscriber(
            id=3,
            clerk_user_id=None,
            email="reader@example.com",
            whatsapp_number="254700000000",
            has_whatsapp_consent=True,
            consented_at="2026-05-13T00:00:00+00:00",
        )
    ]
    monkeypatch.setattr(database_service, "get_connection", _connection)
    monkeypatch.setattr(database_service, "list_consenting_subscribers", lambda connection, article_id: expected)

    assert database_service.get_pending_whatsapp_recipients(7) == expected


def test_get_pending_whatsapp_recipients_logs_and_reraises_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_service, "get_connection", _connection)

    def raise_error(connection: object, article_id: int) -> list[Subscriber]:
        raise RuntimeError("query failed")

    monkeypatch.setattr(database_service, "list_consenting_subscribers", raise_error)

    with pytest.raises(RuntimeError, match="query failed"):
        database_service.get_pending_whatsapp_recipients(7)


def test_mark_whatsapp_summary_sent_marks_notification(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(database_service, "get_connection", _connection)
    monkeypatch.setattr(
        database_service,
        "mark_article_notification_sent",
        lambda connection, article_id, subscriber_id: calls.append((article_id, subscriber_id)),
    )

    database_service.mark_whatsapp_summary_sent(7, 3)

    assert calls == [(7, 3)]


def test_mark_whatsapp_summary_sent_logs_and_reraises_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_service, "get_connection", _connection)

    def raise_error(connection: object, article_id: int, subscriber_id: int) -> None:
        raise RuntimeError("insert failed")

    monkeypatch.setattr(database_service, "mark_article_notification_sent", raise_error)

    with pytest.raises(RuntimeError, match="insert failed"):
        database_service.mark_whatsapp_summary_sent(7, 3)
