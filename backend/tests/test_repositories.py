from pathlib import Path

from app.config import Settings
from app.database import get_connection, init_db
from app.models import ArticleCreate, SubscriberUpsert
from app.repositories import (
    add_chat_message,
    get_article,
    get_latest_notified_article_for_subscriber,
    get_or_create_chat_conversation,
    get_subscriber_by_whatsapp_number,
    list_chat_messages,
    list_articles,
    list_consenting_subscribers,
    mark_article_notification_sent,
    upsert_article,
    upsert_subscriber,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(DATABASE_PATH=tmp_path / "test.db")


def test_article_upsert_and_lookup(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    init_db(settings)
    article = ArticleCreate(
        title="Public Audit Report",
        source="oagkenya.go.ke",
        source_url="https://example.test/report.pdf",
        summary="A formal summary.",
        full_text="The complete report text.",
        date="2026-05-13",
        image="https://example.test/image.jpg",
    )

    with get_connection(settings) as connection:
        saved = upsert_article(connection, article)
        found = get_article(connection, saved.id)
        articles = list_articles(connection)

    assert found == saved
    assert articles == [saved]


def test_consenting_subscribers_excludes_already_notified(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    init_db(settings)

    with get_connection(settings) as connection:
        article = upsert_article(
            connection,
            ArticleCreate(
                title="National Assembly Bill",
                source="parliament.go.ke",
                source_url="https://example.test/bill",
                summary="A formal summary.",
                full_text="The complete bill text.",
                date="2026-05-13",
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
        assert list_consenting_subscribers(connection, article.id) == [subscriber]

        mark_article_notification_sent(connection, article.id, subscriber.id)

        assert list_consenting_subscribers(connection, article.id) == []


def test_latest_notified_article_and_chat_history(tmp_path: Path) -> None:
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
                date="2026-05-14",
                image="",
            ),
        )
        subscriber = upsert_subscriber(
            connection,
            SubscriberUpsert(
                email="reader@example.com",
                whatsapp_number="+254 700-000-000",
                has_whatsapp_consent=True,
            ),
        )
        mark_article_notification_sent(connection, article.id, subscriber.id)

        found_subscriber = get_subscriber_by_whatsapp_number(connection, "254700000000")
        found_article = get_latest_notified_article_for_subscriber(connection, subscriber.id)
        conversation_id = get_or_create_chat_conversation(connection, subscriber.id, article.id)
        add_chat_message(connection, conversation_id, "user", "What changed?", "wamid.1")
        add_chat_message(connection, conversation_id, "assistant", "The summary says...")

        assert found_subscriber == subscriber
        assert found_article == article
        assert list_chat_messages(connection, conversation_id) == [
            {"role": "user", "content": "What changed?"},
            {"role": "assistant", "content": "The summary says..."},
        ]
